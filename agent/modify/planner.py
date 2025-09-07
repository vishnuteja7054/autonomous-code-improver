"""
Planner for creating refactoring and feature implementation plans.
"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from agent.core.models import RefactorPlan, Language, RepoSpec, Severity
from agent.llm.client import LLMClient
from agent.llm.prompt_templates import PromptTemplates


def create_refactor_plan(
    repo_path: str,
    repo_spec: RepoSpec,
    file_path: str,
    code: str,
    context: str,
    llm_client: LLMClient
) -> Optional[RefactorPlan]:
    """
    Create a refactoring plan for a code file.
    
    Args:
        repo_path: Path to the repository
        repo_spec: Repository specification
        file_path: Path to the file to refactor
        code: Code content
        context: Context for the refactoring
        llm_client: LLM client for generating the plan
        
    Returns:
        Refactoring plan or None if generation failed
    """
    logger.info(f"Creating refactoring plan for {file_path}")
    
    try:
        # Determine language
        language = _detect_language_from_path(file_path)
        if not language:
            logger.error(f"Could not determine language for {file_path}")
            return None
            
        # Prepare prompt
        prompt = PromptTemplates.render_template(
            "refactoring",
            language=language.value,
            file_path=file_path,
            code=code,
            context=context
        )
        
        # Generate response
        response = llm_client.generate_structured(
            prompt,
            schema={
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "impact": {"type": "string"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                            }
                        }
                    },
                    "refactoring_plan": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "code_changes": {"type": "string"},
                                "benefits": {"type": "array", "items": {"type": "string"}},
                                "risks": {"type": "array", "items": {"type": "string"}},
                                "mitigations": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "estimated_effort": {"type": "string", "enum": ["low", "medium", "high"]},
                    "overall_risk": {"type": "string", "enum": ["low", "medium", "high"]}
                },
                "required": ["issues", "refactoring_plan", "estimated_effort", "overall_risk"]
            }
        )
        
        # Create refactoring plan
        plan = RefactorPlan(
            repo_id=repo_spec.id,
            title=f"Refactoring plan for {file_path}",
            description=f"Refactoring plan to improve code quality and maintainability",
            target_files=[file_path],
            risk_level=Severity(response.get("overall_risk", "medium")),
            estimated_effort=response.get("estimated_effort", "medium"),
            changes=response.get("refactoring_plan", [])
        )
        
        logger.info(f"Created refactoring plan with {len(plan.changes)} changes")
        return plan
        
    except Exception as e:
        logger.error(f"Error creating refactoring plan: {e}")
        return None


def _detect_language_from_path(file_path: str) -> Optional[Language]:
    """
    Detect the programming language from a file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language or None if not supported
    """
    ext = file_path.split(".")[-1].lower()
    
    language_map = {
        "py": Language.PYTHON,
        "js": Language.JAVASCRIPT,
        "ts": Language.TYPESCRIPT,
        "jsx": Language.JAVASCRIPT,
        "tsx": Language.TYPESCRIPT,
        "java": Language.JAVA,
        "go": Language.GO,
        "rs": Language.RUST,
        "c": Language.C,
        "cpp": Language.CPP,
        "cc": Language.CPP,
        "cxx": Language.CPP,
        "c++": Language.CPP,
        "h": Language.CPP,
        "hpp": Language.CPP,
        "cs": Language.CSHARP,
    }
    
    return language_map.get(ext)
