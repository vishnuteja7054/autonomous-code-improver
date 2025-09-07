"""
Client for interacting with LLM services.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from circuitbreaker import circuit
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from agent.core.models import LLMRequest


class LLMClient:
    """
    Client for interacting with LLM services.
    """
    
    def __init__(self, endpoint: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the LLM client.
        
        Args:
            endpoint: LLM service endpoint
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"Content-Type": "application/json"}
        )
        
        if api_key:
            self.client.headers["Authorization"] = f"Bearer {api_key}"
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    @circuit(failure_threshold=5, recovery_timeout=30)
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated response
        """
        # Prepare request data
        data = {
            "prompt": prompt,
            **kwargs
        }
        
        # Set defaults
        if "temperature" not in data:
            data["temperature"] = 0.7
        if "max_tokens" not in data:
            data["max_tokens"] = 2048
            
        # Log request (without sensitive data)
        logger.debug(f"Sending request to LLM: {self.endpoint}")
        
        # Make request
        start_time = time.time()
        try:
            response = self.client.post(self.endpoint, json=data)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            response_text = result.get("text", "")
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log success
            logger.debug(f"Received response from LLM in {response_time_ms}ms")
            
            return response_text
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to LLM: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise
            
    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate a structured response from the LLM.
        
        Args:
            prompt: Input prompt
            schema: JSON schema for the expected response
            **kwargs: Additional parameters
            
        Returns:
            Structured response as a dictionary
        """
        # Add schema information to the prompt
        schema_prompt = f"""
        {prompt}
        
        Please respond with a JSON object that conforms to the following schema:
        {json.dumps(schema, indent=2)}
        """
        
        # Generate response
        response_text = self.generate(schema_prompt, **kwargs)
        
        # Parse JSON response
        try:
            # Extract JSON from the response (in case there's additional text)
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
                
            json_text = response_text[start_idx:end_idx]
            result = json.loads(json_text)
            
            return result
            
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured response: {e}")
            logger.debug(f"Raw response: {response_text}")
            
            # Try to recover with a simpler approach
            return self._fallback_structured_response(response_text, schema)
            
    def generate_with_guardrails(
        self, 
        prompt: str, 
        guardrails: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response with guardrails applied.
        
        Args:
            prompt: Input prompt
            guardrails: Guardrail configuration
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and guardrail results
        """
        # Apply guardrails to the prompt
        guarded_prompt = self._apply_guardrails(prompt, guardrails)
        
        # Generate response
        response_text = self.generate(guarded_prompt, **kwargs)
        
        # Check guardrails on the response
        guardrail_results = self._check_response_guardrails(response_text, guardrails)
        
        return {
            "response": response_text,
            "guardrails": guardrail_results,
            "passed": all(result.get("passed", True) for result in guardrail_results.values())
        }
        
    def _apply_guardrails(self, prompt: str, guardrails: Dict[str, Any]) -> str:
        """
        Apply guardrails to the prompt.
        
        Args:
            prompt: Original prompt
            guardrails: Guardrail configuration
            
        Returns:
            Guarded prompt
        """
        guarded_prompt = prompt
        
        # Add system instructions
        system_instructions = guardrails.get("system_instructions", [])
        if system_instructions:
            guarded_prompt = "\n".join(system_instructions) + "\n\n" + guarded_prompt
            
        # Add forbidden content warning
        forbidden_content = guardrails.get("forbidden_content", [])
        if forbidden_content:
            forbidden_text = ", ".join(forbidden_content)
            guarded_prompt += f"\n\nDo not include any of the following in your response: {forbidden_text}"
            
        # Add format instructions
        format_instructions = guardrails.get("format_instructions", "")
        if format_instructions:
            guarded_prompt += f"\n\n{format_instructions}"
            
        return guarded_prompt
        
    def _check_response_guardrails(self, response: str, guardrails: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the response passes guardrails.
        
        Args:
            response: Generated response
            guardrails: Guardrail configuration
            
        Returns:
            Dictionary with guardrail check results
        """
        results = {}
        
        # Check for forbidden content
        forbidden_content = guardrails.get("forbidden_content", [])
        if forbidden_content:
            results["forbidden_content"] = {
                "passed": True,
                "details": []
            }
            
            for item in forbidden_content:
                if item.lower() in response.lower():
                    results["forbidden_content"]["passed"] = False
                    results["forbidden_content"]["details"].append(f"Found forbidden content: {item}")
                    
        # Check response length
        max_length = guardrails.get("max_response_length")
        if max_length:
            results["response_length"] = {
                "passed": len(response) <= max_length,
                "details": f"Response length: {len(response)}, max allowed: {max_length}"
            }
            
        # Check for required content
        required_content = guardrails.get("required_content", [])
        if required_content:
            results["required_content"] = {
                "passed": True,
                "details": []
            }
            
            for item in required_content:
                if item.lower() not in response.lower():
                    results["required_content"]["passed"] = False
                    results["required_content"]["details"].append(f"Missing required content: {item}")
                    
        return results
        
    def log_request(self, request: LLMRequest, response: Optional[str] = None) -> None:
        """
        Log an LLM request and response.
        
        Args:
            request: LLM request object
            response: Response text (if available)
        """
        # Sanitize prompt for logging (remove sensitive information)
        sanitized_prompt = self._sanitize_prompt(request.prompt)
        
        log_data = {
            "request_id": str(request.id),
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "prompt_length": len(request.prompt),
            "response_length": len(response) if response else 0,
            "response_time_ms": request.response_time_ms,
            "tokens_used": request.tokens_used,
            "error": request.error_message,
        }
        
        if response:
            # Log a summary of the response (not the full content)
            response_summary = response[:100] + "..." if len(response) > 100 else response
            log_data["response_summary"] = response_summary
            
        logger.info(f"LLM request: {json.dumps(log_data)}")
        
    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize a prompt for logging.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Sanitized prompt
        """
        # Remove potential sensitive information
        # This is a simple implementation - in production you might want more sophisticated sanitization
        
        # Remove API keys
        import re
        sanitized = re.sub(r'(api[_-]?key|password|secret)\s*[:=]\s*[\'"]\w+[\'"]', '[REDACTED]', prompt, flags=re.IGNORECASE)
        
        # Remove URLs that might contain sensitive information
        sanitized = re.sub(r'https?://[^\s<>"{}|\\^`\[\]]+', '[URL]', sanitized)
        
        return sanitized
