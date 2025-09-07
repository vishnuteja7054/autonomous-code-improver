"""
Configuration for LLM components.
"""

import os
from typing import Optional

from pydantic import BaseSettings, Field


class LLMConfig(BaseSettings):
    """Configuration for LLM components."""
    
    endpoint: str = Field(default="http://localhost:8000/v1", description="LLM service endpoint")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    temperature: float = Field(default=0.7, description="Default temperature for generation")
    max_tokens: int = Field(default=2048, description="Default maximum tokens for generation")
    
    # Circuit breaker settings
    circuit_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_recovery_timeout: int = Field(default=30, description="Circuit breaker recovery timeout in seconds")
    
    # Guardrails settings
    enable_guardrails: bool = Field(default=True, description="Enable guardrails")
    max_response_length: int = Field(default=10000, description="Maximum response length")
    
    # Logging settings
    log_requests: bool = Field(default=True, description="Log LLM requests")
    log_responses: bool = Field(default=False, description="Log LLM responses")
    
    class Config:
        env_prefix = "LLM_"
        env_file = ".env"


# Global configuration instance
config = LLMConfig()


def get_config() -> LLMConfig:
    """Get the global LLM configuration."""
    return config
