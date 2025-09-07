
## agent/llm/tests/test_llm_client.py

```python
"""
Tests for LLM client functionality.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from agent.llm.client import LLMClient
from agent.core.models import LLMRequest


class TestLLMClient(unittest.TestCase):
    """Test cases for LLM client."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = LLMClient(
            endpoint="http://localhost:8000/v1",
            api_key="test-api-key",
            timeout=30
        )

    @patch('agent.llm.client.httpx.Client')
    def test_generate(self, mock_client_class):
        """Test generating a response from the LLM."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Generated response"}
        mock_client.post.return_value = mock_response
        
        # Call function
        response = self.client.generate("Test prompt", temperature=0.5, max_tokens=100)
        
        # Assertions
        self.assertEqual(response, "Generated response")
        mock_client.post.assert_called_once()
        
        # Check request data
        call_args = mock_client.post.call_args
        self.assertEqual(call_args[1]["json"]["prompt"], "Test prompt")
        self.assertEqual(call_args[1]["json"]["temperature"], 0.5)
        self.assertEqual(call_args[1]["json"]["max_tokens"], 100)

    @patch('agent.llm.client.httpx.Client')
    def test_generate_structured(self, mock_client_class):
        """Test generating a structured response from the LLM."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": '{"name": "test", "value": 42}'}
        mock_client.post.return_value = mock_response
        
        # Create schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }
        
        # Call function
        response = self.client.generate_structured("Test prompt", schema)
        
        # Assertions
        self.assertEqual(response, {"name": "test", "value": 42})
        mock_client.post.assert_called_once()

    @patch('agent.llm.client.httpx.Client')
    def test_generate_structured_fallback(self, mock_client_class):
        """Test fallback parsing for structured responses."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Here's the response: name: test, value: 42"}
        mock_client.post.return_value = mock_response
        
        # Create schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }
        
        # Call function
        response = self.client.generate_structured("Test prompt", schema)
        
        # Assertions
        self.assertEqual(response["name"], "test")
        self.assertEqual(response["value"], 42)
        mock_client.post.assert_called_once()

    @patch('agent.llm.client.httpx.Client')
    def test_generate_with_guardrails(self, mock_client_class):
        """Test generating a response with guardrails."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Generated response without forbidden content"}
        mock_client.post.return_value = mock_response
        
        # Create guardrails
        guardrails = {
            "system_instructions": ["You are a helpful assistant."],
            "forbidden_content": ["password", "secret"],
            "max_response_length": 1000,
            "required_content": ["helpful"]
        }
        
        # Call function
        response = self.client.generate_with_guardrails("Test prompt", guardrails)
        
        # Assertions
        self.assertTrue(response["passed"])
        self.assertEqual(response["response"], "Generated response without forbidden content")
        mock_client.post.assert_called_once()
        
        # Check that the prompt was modified
        call_args = mock_client.post.call_args
        prompt = call_args[1]["json"]["prompt"]
        self.assertIn("You are a helpful assistant.", prompt)
        self.assertIn("Do not include any of the following in your response: password, secret", prompt)

    @patch('agent.llm.client.httpx.Client')
    def test_generate_with_guardrails_failure(self, mock_client_class):
        """Test generating a response with guardrails that fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Generated response with password and secret"}
        mock_client.post.return_value = mock_response
        
        # Create guardrails
        guardrails = {
            "forbidden_content": ["password", "secret"],
            "max_response_length": 1000,
            "required_content": ["helpful"]
        }
        
        # Call function
        response = self.client.generate_with_guardrails("Test prompt", guardrails)
        
        # Assertions
        self.assertFalse(response["passed"])
        self.assertIn("forbidden_content", response["guardrails"])
        self.assertFalse(response["guardrails"]["forbidden_content"]["passed"])
        self.assertIn("Found forbidden content: password", response["guardrails"]["forbidden_content"]["details"])

    def test_sanitize_prompt(self):
        """Test prompt sanitization."""
        # Test with API key
        prompt = "Here's my API key: api_key='1234567890'"
        sanitized = self.client._sanitize_prompt(prompt)
        self.assertEqual(sanitized, "Here's my API key: [REDACTED]")
        
        # Test with password
        prompt = "The password is secret='my-password'"
        sanitized = self.client._sanitize_prompt(prompt)
        self.assertEqual(sanitized, "The password is [REDACTED]")
        
        # Test with URL
        prompt = "Check out https://example.com/api?key=123"
        sanitized = self.client._sanitize_prompt(prompt)
        self.assertEqual(sanitized, "Check out [URL]")

    @patch('agent.llm.client.logger')
    def test_log_request(self, mock_logger):
        """Test logging an LLM request."""
        # Create request
        request = LLMRequest(
            prompt="Test prompt with api_key='secret'",
            model="test-model",
            temperature=0.7,
            max_tokens=100
        )
        
        # Log request
        self.client.log_request(request, "Test response")
        
        # Assertions
        mock_logger.info.assert_called_once()
        
        # Check that the prompt was sanitized
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("api_key=[REDACTED]", call_args)


if __name__ == "__main__":
    unittest.main()
