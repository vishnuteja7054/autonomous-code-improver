"""
LLM module for interacting with language models.
"""

from .client import LLMClient
from .prompt_templates import PromptTemplates

__all__ = ["LLMClient", "PromptTemplates"]
