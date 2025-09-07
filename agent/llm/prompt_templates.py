"""
Prompt templates for different agents.
"""

import json
from typing import Any, Dict, List, Optional

from jinja2 import Template


class PromptTemplates:
    """
    Collection of prompt templates for different agents.
    """
    
    @staticmethod
    def code_review_template() -> Template:
        """
        Template for code review prompts.
        """
        template_str = """
You are an expert code reviewer. Please review the following code and identify any issues:

Language: {{ language }}
File: {{ file_path }}
Code:
```{{ language }}
{{ code }}  
Please provide a detailed review focusing on: 

     Code quality and readability
     Potential bugs or errors
     Security vulnerabilities
     Performance issues
     Best practices violations
     

For each issue, provide: 

     Severity level (low, medium, high, critical)
     A clear description of the issue
     Suggested fix or improvement
     

Format your response as a JSON object with the following structure:
{
  "issues": [
    {
      "severity": "high",
      "type": "security",
      "title": "Issue title",
      "description": "Detailed description of the issue",
      "line_number": 123,
      "suggested_fix": "Code or description of the fix"
    }
  ],
  "overall_assessment": "Overall assessment of the code quality",
  "recommendations": ["List of general recommendations"]
}
"""
        return Template(template_str) 
@staticmethod
def refactoring_template() -> Template:
    """
    Template for refactoring prompts.
    """
    template_str = """

You are an expert software architect specializing in code refactoring. Please analyze the following code and suggest refactoring improvements: 

Language: {{ language }}
File: {{ file_path }}
{{ code }}
Context: {{ context }} 

Please provide a refactoring plan that: 

     Identifies specific issues with the current code structure
     Proposes concrete refactoring changes
     Explains the benefits of each change
     Considers potential risks and mitigations
     

Format your response as a JSON object with the following structure:
{
  "issues": [
    {
      "type": "architecture|design|performance|maintainability",
      "description": "Description of the issue",
      "impact": "Impact of the issue",
      "priority": "low|medium|high"
    }
  ],
  "refactoring_plan": [
    {
      "title": "Refactoring step title",
      "description": "Detailed description of the refactoring step",
      "code_changes": "Specific code changes needed",
      "benefits": ["Benefit 1", "Benefit 2"],
      "risks": ["Risk 1", "Risk 2"],
      "mitigations": ["Mitigation 1", "Mitigation 2"]
    }
  ],
  "estimated_effort": "low|medium|high",
  "overall_risk": "low|medium|high"
}
"""
        return Template(template_str) 
@staticmethod
def feature_proposal_template() -> Template:
    """
    Template for feature proposal prompts.
    """
    template_str = """

You are an innovative software engineer. Based on the following codebase context, propose a new feature that would add value: 

Repository: {{ repo_name }}
Primary language: {{ language }}
Codebase summary: {{ codebase_summary }}
Current issues or limitations: {{ current_issues }} 

Please propose a new feature that: 

     Addresses a specific need or opportunity
     Is feasible to implement
     Provides clear value to users or developers
     Aligns with the codebase architecture
     

Format your response as a JSON object with the following structure:
{
  "feature_title": "Title of the proposed feature",
  "description": "Detailed description of the feature",
  "rationale": "Why this feature is valuable and necessary",
  "acceptance_criteria": [
    "Criterion 1",
    "Criterion 2"
  ],
  "implementation_approach": "High-level approach to implementation",
  "estimated_effort": "low|medium|high",
  "benefits": ["Benefit 1", "Benefit 2"],
  "risks": ["Risk 1", "Risk 2"],
  "dependencies": ["Dependency 1", "Dependency 2"]
}
"""
        return Template(template_str) 
@staticmethod
def test_generation_template() -> Template:
    """
    Template for test generation prompts.
    """
    template_str = """

You are an expert in test-driven development. Please generate comprehensive tests for the following code: 

Language: {{ language }}
File: {{ file_path }}
Function/Class: {{ function_name }}
{{ code }}
Please generate tests that: 

     Cover all main functionality
     Include edge cases and error conditions
     Follow best practices for testing
     Are clear and maintainable
     

Format your response as a JSON object with the following structure:
{
  "test_cases": [
    {
      "description": "Description of what the test verifies",
      "test_code": "{{ language }}\nTest code here\n",
      "type": "unit|integration|e2e",
      "priority": "high|medium|low"
    }
  ],
  "test_framework": "{{ test_framework }}",
  "coverage_estimate": "Estimated percentage of code coverage",
  "additional_setup": "Any additional setup required"
}
"""
        return Template(template_str) 
@staticmethod
def documentation_generation_template() -> Template:
    """
    Template for documentation generation prompts.
    """
    template_str = """

You are a technical writer. Please generate comprehensive documentation for the following code: 

Language: {{ language }}
File: {{ file_path }}
Code: 
{{ code }}
Please generate documentation that: 

     Clearly explains what the code does
     Describes the parameters and return values
     Includes usage examples
     Notes any important considerations or limitations
     

Format your response as a JSON object with the following structure:
{
  "summary": "Brief summary of the code's purpose",
  "detailed_description": "Detailed description of functionality",
  "parameters": [
    {
      "name": "param_name",
      "type": "param_type",
      "description": "Parameter description",
      "required": true
    }
  ],
  "returns": {
    "type": "return_type",
    "description": "Description of return value"
  },
  "examples": [
    {
      "description": "Example description",
      "code": "{{ language }}\nExample code\n"
    }
  ],
  "notes": ["Important note 1", "Important note 2"]
}
"""
        return Template(template_str) 
@staticmethod
def security_analysis_template() -> Template:
    """
    Template for security analysis prompts.
    """
    template_str = """

You are a security expert. Please analyze the following code for security vulnerabilities: 

Language: {{ language }}
File: {{ file_path }}
{{ code }}
Context: {{ context }} 

Please identify potential security issues including: 

     Input validation problems
     Authentication/authorization issues
     Data exposure risks
     Injection vulnerabilities
     Cryptographic weaknesses
     Other security concerns
     

Format your response as a JSON object with the following structure:
{
  "vulnerabilities": [
    {
      "type": "injection|auth|crypto|validation|other",
      "severity": "low|medium|high|critical",
      "title": "Vulnerability title",
      "description": "Detailed description of the vulnerability",
      "line_number": 123,
      "impact": "Potential impact of the vulnerability",
      "remediation": "How to fix the vulnerability"
    }
  ],
  "overall_security_rating": "poor|fair|good|excellent",
  "recommendations": ["Security recommendation 1", "Security recommendation 2"]
}
"""
        return Template(template_str) 
@staticmethod
def performance_analysis_template() -> Template:
    """
    Template for performance analysis prompts.
    """
    template_str = """

You are a performance optimization expert. Please analyze the following code for performance issues: 

Language: {{ language }}
File: {{ file_path }}
Code: 
{{ code }}
Context: {{ context }} 

Please identify performance issues including: 

     Algorithmic inefficiencies
     Memory usage problems
     I/O bottlenecks
     Concurrency issues
     Other performance concerns
     

Format your response as a JSON object with the following structure:
{
  "issues": [
    {
      "type": "algorithm|memory|io|concurrency|other",
      "severity": "low|medium|high",
      "title": "Performance issue title",
      "description": "Detailed description of the issue",
      "line_number": 123,
      "impact": "Impact on performance",
      "optimization": "How to optimize the code"
    }
  ],
  "overall_performance_rating": "poor|fair|good|excellent",
  "recommendations": ["Performance recommendation 1", "Performance recommendation 2"]
}
"""
        return Template(template_str) 
@staticmethod
def render_template(template_name: str, **kwargs) -> str:
    """
    Render a prompt template with the given parameters.
    
    Args:
        template_name: Name of the template to render
        **kwargs: Template parameters
        
    Returns:
        Rendered prompt string
    """
    templates = {
        "code_review": PromptTemplates.code_review_template(),
        "refactoring": PromptTemplates.refactoring_template(),
        "feature_proposal": PromptTemplates.feature_proposal_template(),
        "test_generation": PromptTemplates.test_generation_template(),
        "documentation": PromptTemplates.documentation_generation_template(),
        "security_analysis": PromptTemplates.security_analysis_template(),
        "performance_analysis": PromptTemplates.performance_analysis_template(),
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}")
        
    template = templates[template_name]
    return template.render(**kwargs)
