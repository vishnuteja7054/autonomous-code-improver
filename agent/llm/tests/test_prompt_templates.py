"""
Tests for prompt templates functionality.
"""

import unittest

from agent.llm.prompt_templates import PromptTemplates


class TestPromptTemplates(unittest.TestCase):
    """Test cases for prompt templates."""

    def test_code_review_template(self):
        """Test code review template."""
        template = PromptTemplates.code_review_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/main.py",
            code="print('Hello, world!')"
        )
        
        # Assertions
        self.assertIn("You are an expert code reviewer", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/main.py", rendered)
        self.assertIn("print('Hello, world!')", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("severity", rendered)
        self.assertIn("type", rendered)
        self.assertIn("title", rendered)

    def test_refactoring_template(self):
        """Test refactoring template."""
        template = PromptTemplates.refactoring_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/main.py",
            code="print('Hello, world!')",
            context="Refactor for better maintainability"
        )
        
        # Assertions
        self.assertIn("expert software architect", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/main.py", rendered)
        self.assertIn("print('Hello, world!')", rendered)
        self.assertIn("Context: Refactor for better maintainability", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("issues", rendered)
        self.assertIn("refactoring_plan", rendered)
        self.assertIn("estimated_effort", rendered)

    def test_feature_proposal_template(self):
        """Test feature proposal template."""
        template = PromptTemplates.feature_proposal_template()
        
        # Render template
        rendered = template.render(
            repo_name="example-repo",
            language="python",
            codebase_summary="A simple Python application",
            current_issues="Lacks caching and logging"
        )
        
        # Assertions
        self.assertIn("innovative software engineer", rendered)
        self.assertIn("Repository: example-repo", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("A simple Python application", rendered)
        self.assertIn("Lacks caching and logging", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("feature_title", rendered)
        self.assertIn("description", rendered)
        self.assertIn("acceptance_criteria", rendered)

    def test_test_generation_template(self):
        """Test test generation template."""
        template = PromptTemplates.test_generation_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/main.py",
            function_name="hello_world",
            code="def hello_world():\n    print('Hello, world!')"
        )
        
        # Assertions
        self.assertIn("test-driven development", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/main.py", rendered)
        self.assertIn("Function/Class: hello_world", rendered)
        self.assertIn("def hello_world():", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("test_cases", rendered)
        self.assertIn("test_framework", rendered)

    def test_documentation_generation_template(self):
        """Test documentation generation template."""
        template = PromptTemplates.documentation_generation_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/main.py",
            code="def hello_world():\n    print('Hello, world!')"
        )
        
        # Assertions
        self.assertIn("technical writer", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/main.py", rendered)
        self.assertIn("def hello_world():", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("summary", rendered)
        self.assertIn("parameters", rendered)
        self.assertIn("returns", rendered)
        self.assertIn("examples", rendered)

    def test_security_analysis_template(self):
        """Test security analysis template."""
        template = PromptTemplates.security_analysis_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/database.py",
            code="query = \"SELECT * FROM users WHERE id = \" + user_id",
            context="User authentication module"
        )
        
        # Assertions
        self.assertIn("security expert", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/database.py", rendered)
        self.assertIn("query = \"SELECT * FROM users WHERE id = \" + user_id", rendered)
        self.assertIn("Context: User authentication module", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("vulnerabilities", rendered)
        self.assertIn("severity", rendered)
        self.assertIn("remediation", rendered)

    def test_performance_analysis_template(self):
        """Test performance analysis template."""
        template = PromptTemplates.performance_analysis_template()
        
        # Render template
        rendered = template.render(
            language="python",
            file_path="src/processing.py",
            code="for i in range(n):\n    for j in range(n):\n        process(i, j)",
            context="Data processing module"
        )
        
        # Assertions
        self.assertIn("performance optimization expert", rendered)
        self.assertIn("Language: python", rendered)
        self.assertIn("File: src/processing.py", rendered)
        self.assertIn("for i in range(n):", rendered)
        self.assertIn("Context: Data processing module", rendered)
        self.assertIn("JSON object", rendered)
        self.assertIn("issues", rendered)
        self.assertIn("severity", rendered)
        self.assertIn("optimization", rendered)

    def test_render_template(self):
        """Test template rendering utility."""
        # Test with valid template name
        rendered = PromptTemplates.render_template(
            "code_review",
            language="python",
            file_path="src/main.py",
            code="print('Hello, world!')"
        )
        
        self.assertIn("You are an expert code reviewer", rendered)
        
        # Test with invalid template name
        with self.assertRaises(ValueError):
            PromptTemplates.render_template(
                "invalid_template",
                language="python",
                file_path="src/main.py",
                code="print('Hello, world!')"
            )


if __name__ == "__main__":
    unittest.main()

