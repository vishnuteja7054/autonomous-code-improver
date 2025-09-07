"""
Utility functions for LLM components.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text.
    
    Args:
        text: Text containing JSON
        
    Returns:
        Extracted JSON object or None if not found
    """
    try:
        # Find JSON object in text
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx == -1 or end_idx == 0:
            return None
            
        json_text = text[start_idx:end_idx]
        return json.loads(json_text)
    except (ValueError, json.JSONDecodeError):
        return None


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from text.
    
    Args:
        text: Text containing code blocks
        
    Returns:
        List of code blocks with language and code
    """
    code_blocks = []
    
    # Pattern to match code blocks
    pattern = r"```(\w+)?\n(.*?)\n```"
    
    matches = re.findall(pattern, text, re.DOTALL)
    
    for language, code in matches:
        code_blocks.append({
            "language": language or "text",
            "code": code.strip()
        })
    
    return code_blocks


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text by removing sensitive information and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    # Remove sensitive information
    sanitized = re.sub(
        r'(api[_-]?key|password|secret|token)\s*[:=]\s*[\'"]\w+[\'"]',
        '[REDACTED]',
        text,
        flags=re.IGNORECASE
    )
    
    # Remove URLs
    sanitized = re.sub(
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        '[URL]',
        sanitized
    )
    
    # Remove email addresses
    sanitized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        sanitized
    )
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def count_tokens(text: str) -> int:
    """
    Count tokens in text (approximate).
    
    Args:
        text: Text to count tokens in
        
    Returns:
        Approximate token count
    """
    # Simple approximation: 1 token ≈ 4 characters for English text
    return len(text) // 4


def truncate_prompt(prompt: str, max_tokens: int) -> str:
    """
    Truncate prompt to fit within token limit.
    
    Args:
        prompt: Prompt to truncate
        max_tokens: Maximum allowed tokens
        
    Returns:
        Truncated prompt
    """
    # Estimate current token count
    current_tokens = count_tokens(prompt)
    
    if current_tokens <= max_tokens:
        return prompt
    
    # Calculate truncation ratio
    ratio = max_tokens / current_tokens
    
    # Truncate text proportionally
    truncated_length = int(len(prompt) * ratio)
    truncated = prompt[:truncated_length]
    
    # Ensure we don't cut off in the middle of a word
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + "..."


def merge_prompt_and_context(prompt: str, context: str, max_tokens: int) -> str:
    """
    Merge prompt and context while respecting token limit.
    
    Args:
        prompt: Main prompt
        context: Additional context
        max_tokens: Maximum allowed tokens
        
    Returns:
        Merged prompt and context
    """
    # Estimate token counts
    prompt_tokens = count_tokens(prompt)
    context_tokens = count_tokens(context)
    
    if prompt_tokens + context_tokens <= max_tokens:
        return f"{prompt}\n\nContext:\n{context}"
    
    # If context is too long, prioritize prompt
    if prompt_tokens > max_tokens:
        return truncate_prompt(prompt, max_tokens)
    
    # Calculate available tokens for context
    available_tokens = max_tokens - prompt_tokens
    
    # Truncate context to fit
    truncated_context = truncate_prompt(context, available_tokens)
    
    return f"{prompt}\n\nContext:\n{truncated_context}"


def format_findings_for_llm(findings: List[Dict[str, Any]]) -> str:
    """
    Format findings for LLM consumption.
    
    Args:
        findings: List of findings
        
    Returns:
        Formatted findings string
    """
    if not findings:
        return "No findings identified."
    
    formatted = "Identified findings:\n\n"
    
    for i, finding in enumerate(findings, 1):
        formatted += f"{i}. {finding.get('title', 'Untitled')}\n"
        formatted += f"   Type: {finding.get('type', 'Unknown')}\n"
        formatted += f"   Severity: {finding.get('severity', 'Unknown')}\n"
        formatted += f"   Description: {finding.get('description', 'No description')}\n"
        
        if finding.get('file_path'):
            formatted += f"   File: {finding['file_path']}\n"
            
        if finding.get('line_number'):
            formatted += f"   Line: {finding['line_number']}\n"
            
        formatted += "\n"
    
    return formatted


def format_code_for_llm(code: str, language: str = "python") -> str:
    """
    Format code for LLM consumption.
    
    Args:
        code: Code to format
        language: Programming language
        
    Returns:
        Formatted code string
    """
    return f"```{language}\n{code}\n```"


def parse_structured_response(
    response: str, 
    expected_keys: List[str]
) -> Dict[str, Any]:
    """
    Parse a structured response from LLM.
    
    Args:
        response: Response text from LLM
        expected_keys: List of expected keys in the response
        
    Returns:
        Parsed response as dictionary
    """
    # Try to extract JSON first
    result = extract_json_from_text(response)
    
    if result:
        return result
    
    # Fallback: parse key-value pairs manually
    parsed = {}
    
    for key in expected_keys:
        # Look for patterns like "key: value" or "key = value"
        patterns = [
            rf"{re.escape(key)}:\s*(.+?)(?=\n\s*[A-Za-z_]|$)",
            rf"{re.escape(key)}\s*=\s*(.+?)(?=\n\s*[A-Za-z_]|$)",
            rf'"{re.escape(key)}":\s*"(.+?)"(?=\s*,|\s*}})',
            rf"'{re.escape(key)}':\s*'(.+?)'(?=\s*,|\s*}})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                
                # Try to parse as JSON if it looks like a complex value
                if value.startswith("{") or value.startswith("["):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                        
                parsed[key] = break
    
    # Fill in missing keys with default values
    for key in expected_keys:
        if key not in parsed:
            parsed[key] = None
    
    return parsed


def validate_structured_response(
    response: Dict[str, Any], 
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate a structured response against a schema.
    
    Args:
        response: Response to validate
        schema: JSON schema to validate against
        
    Returns:
        Validation result with valid flag and errors
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in response or response[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Check field types
    properties = schema.get("properties", {})
    for field, value in response.items():
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get("type")
            
            if field_type and not isinstance(value, eval(field_type)):
                errors.append(f"Field '{field}' should be of type {field_type}")
    
    # Check enum values
    for field, value in response.items():
        if field in properties and "enum" in properties[field]:
            valid_values = properties[field]["enum"]
            if value not in valid_values:
                errors.append(f"Field '{field}' should be one of {valid_values}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
