"""
Factory for creating LLM clients with different configurations.
"""

from typing import Dict, Any, Optional

from agent.llm.client import LLMClient
from agent.llm.config import get_config


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMClient:
        """
        Create an LLM client with the specified configuration.
        
        Args:
            endpoint: LLM service endpoint (overrides config)
            api_key: API key for authentication (overrides config)
            timeout: Request timeout in seconds (overrides config)
            **kwargs: Additional configuration options
            
        Returns:
            Configured LLM client
        """
        config = get_config()
        
        # Use provided values or fall back to config
        client_endpoint = endpoint or config.endpoint
        client_api_key = api_key or config.api_key
        client_timeout = timeout or config.timeout
        
        return LLMClient(
            endpoint=client_endpoint,
            api_key=client_api_key,
            timeout=client_timeout,
            **kwargs
        )
    
    @staticmethod
    def create_client_for_purpose(purpose: str) -> LLMClient:
        """
        Create an LLM client optimized for a specific purpose.
        
        Args:
            purpose: Purpose of the client (e.g., "code_review", "refactoring")
            
        Returns:
            Optimized LLM client
        """
        config = get_config()
        
        # Default configuration
        client_config = {
            "endpoint": config.endpoint,
            "api_key": config.api_key,
            "timeout": config.timeout,
        }
        
        # Adjust configuration based on purpose
        if purpose == "code_review":
            client_config.update({
                "temperature": 0.3,  # Lower temperature for more consistent results
                "max_tokens": 3000,  # Allow longer responses for detailed reviews
            })
        elif purpose == "refactoring":
            client_config.update({
                "temperature": 0.5,  # Moderate temperature for creative solutions
                "max_tokens": 4000,  # Allow longer responses for detailed plans
            })
        elif purpose == "feature_proposal":
            client_config.update({
                "temperature": 0.8,  # Higher temperature for creative ideas
                "max_tokens": 3000,  # Allow detailed proposals
            })
        elif purpose == "test_generation":
            client_config.update({
                "temperature": 0.2,  # Low temperature for consistent test code
                "max_tokens": 4000,  # Allow comprehensive test suites
            })
        elif purpose == "documentation":
            client_config.update({
                "temperature": 0.4,  # Moderate temperature for clear explanations
                "max_tokens": 3000,  # Allow detailed documentation
            })
        elif purpose == "security_analysis":
            client_config.update({
                "temperature": 0.2,  # Low temperature for precise analysis
                "max_tokens": 3000,  # Allow detailed security reports
            })
        elif purpose == "performance_analysis":
            client_config.update({
                "temperature": 0.3,  # Low temperature for precise analysis
                "max_tokens": 3000,  # Allow detailed performance reports
            })
        
        return LLMClient(**client_config)
    
    @staticmethod
    def create_clients_for_purposes(purposes: Dict[str, str]) -> Dict[str, LLMClient]:
        """
        Create multiple LLM clients for different purposes.
        
        Args:
            purposes: Dictionary mapping purpose names to purpose types
            
        Returns:
            Dictionary mapping purpose names to LLM clients
        """
        clients = {}
        
        for name, purpose in purposes.items():
            clients[name] = LLMClientFactory.create_client_for_purpose(purpose)
        
        return clients
