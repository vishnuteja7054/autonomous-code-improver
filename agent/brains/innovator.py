"""
Innovator agent for discovering and proposing new features.
"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from agent.core.models import FeatureProposal, Language, RepoSpec, Severity
from agent.llm.client import LLMClient
from agent.llm.prompt_templates import PromptTemplates


class Innovator:
    """
    Agent for discovering and proposing new features.
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the innovator.
        
        Args:
            llm_client: LLM client for generating feature proposals
        """
        self.llm_client = llm_client
        
    def discover_features(
        self, 
        repo_path: str, 
        repo_spec: RepoSpec,
        codebase_summary: str,
        current_issues: List[str]
    ) -> List[FeatureProposal]:
        """
        Discover and propose new features for a repository.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            codebase_summary: Summary of the codebase
            current_issues: List of current issues or limitations
            
        Returns:
            List of feature proposals
        """
        logger.info("Discovering new features")
        
        proposals = []
        
        # Generate feature proposals using LLM
        for language in repo_spec.languages or [Language.PYTHON]:
            proposal = self._generate_feature_proposal(
                repo_spec, 
                language, 
                codebase_summary, 
                current_issues
            )
            
            if proposal:
                proposals.append(proposal)
                
        logger.info(f"Generated {len(proposals)} feature proposals")
        return proposals
        
    def _generate_feature_proposal(
        self, 
        repo_spec: RepoSpec,
        language: Language,
        codebase_summary: str,
        current_issues: List[str]
    ) -> Optional[FeatureProposal]:
        """
        Generate a feature proposal using the LLM.
        
        Args:
            repo_spec: Repository specification
            language: Programming language
            codebase_summary: Summary of the codebase
            current_issues: List of current issues or limitations
            
        Returns:
            Feature proposal or None if generation failed
        """
        try:
            # Prepare prompt
            prompt = PromptTemplates.render_template(
                "feature_proposal",
                repo_name=repo_spec.url.split("/")[-1],
                language=language.value,
                codebase_summary=codebase_summary,
                current_issues="\n".join(current_issues)
            )
            
            # Generate response
            response = self.llm_client.generate_structured(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "feature_title": {"type": "string"},
                        "description": {"type": "string"},
                        "rationale": {"type": "string"},
                        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                        "implementation_approach": {"type": "string"},
                        "estimated_effort": {"type": "string", "enum": ["low", "medium", "high"]},
                        "benefits": {"type": "array", "items": {"type": "string"}},
                        "risks": {"type": "array", "items": {"type": "string"}},
                        "dependencies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["feature_title", "description", "rationale", "acceptance_criteria"]
                }
            )
            
            # Create feature proposal
            proposal = FeatureProposal(
                repo_id=repo_spec.id,
                title=response.get("feature_title", ""),
                description=response.get("description", ""),
                rationale=response.get("rationale", ""),
                acceptance_criteria=response.get("acceptance_criteria", []),
                estimated_effort=response.get("estimated_effort", "medium"),
                risk_level=self._assess_risk_level(response.get("risks", [])),
                cost_benefit_analysis={
                    "benefits": response.get("benefits", []),
                    "risks": response.get("risks", []),
                    "estimated_effort": response.get("estimated_effort", "medium")
                },
                testability_notes=self._assess_testability(response.get("acceptance_criteria", []))
            )
            
            return proposal
            
        except Exception as e:
            logger.error(f"Error generating feature proposal: {e}")
            return None
            
    def _assess_risk_level(self, risks: List[str]) -> Severity:
        """
        Assess the risk level based on identified risks.
        
        Args:
            risks: List of identified risks
            
        Returns:
            Severity level
        """
        if not risks:
            return Severity.LOW
            
        # Count high-impact risk keywords
        high_impact_keywords = [
            "security", "breaking", "data loss", "performance", "scalability",
            "compatibility", "migration", "downtime"
        ]
        
        high_risk_count = 0
        for risk in risks:
            for keyword in high_impact_keywords:
                if keyword.lower() in risk.lower():
                    high_risk_count += 1
                    break
                    
        if high_risk_count >= 2:
            return Severity.HIGH
        elif high_risk_count >= 1:
            return Severity.MEDIUM
        else:
            return Severity.LOW
            
    def _assess_testability(self, acceptance_criteria: List[str]) -> Optional[str]:
        """
        Assess the testability of a feature based on its acceptance criteria.
        
        Args:
            acceptance_criteria: List of acceptance criteria
            
        Returns:
            Testability assessment notes or None
        """
        if not acceptance_criteria:
            return "No acceptance criteria provided - testability cannot be assessed"
            
        # Check for measurable criteria
        measurable_keywords = [
            "should", "must", "will", "verify", "validate", "check", "ensure"
        ]
        
        measurable_count = 0
        for criterion in acceptance_criteria:
            for keyword in measurable_keywords:
                if keyword.lower() in criterion.lower():
                    measurable_count += 1
                    break
                    
        testability_ratio = measurable_count / len(acceptance_criteria)
        
        if testability_ratio >= 0.8:
            return "High testability - most criteria are measurable and verifiable"
        elif testability_ratio >= 0.5:
            return "Medium testability - some criteria may need clarification for testing"
        else:
            return "Low testability - many criteria are vague or not easily testable"
