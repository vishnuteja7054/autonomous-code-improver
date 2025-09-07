"""
Mutation testing for evaluating test suite effectiveness.
"""

import json
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agent.core.models import Finding, FindingType, Language, RepoSpec, Severity


class MutationTester:
    """
    Mutation testing for evaluating test suite effectiveness.
    """
    
    def __init__(self):
        """Initialize the mutation tester."""
        self.supported_languages = [Language.PYTHON]
        
    def test(self, repo_path: str, repo_spec: RepoSpec) -> Dict[str, Any]:
        """
        Run mutation testing on a repository.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            Dictionary with mutation testing results
        """
        results = {
            "mutation_score": 0.0,
            "total_mutants": 0,
            "killed_mutants": 0,
            "survived_mutants": 0,
            "timeout_mutants": 0,
            "findings": []
        }
        
        # Run language-specific mutation testing
        for language in repo_spec.languages or self.supported_languages:
            if language == Language.PYTHON:
                lang_results = self._test_python(repo_path, repo_spec)
                results["findings"].extend(lang_results["findings"])
                
                # Aggregate results
                results["total_mutants"] += lang_results["total_mutants"]
                results["killed_mutants"] += lang_results["killed_mutants"]
                results["survived_mutants"] += lang_results["survived_mutants"]
                results["timeout_mutants"] += lang_results["timeout_mutants"]
                
        # Calculate mutation score
        if results["total_mutants"] > 0:
            results["mutation_score"] = results["killed_mutants"] / results["total_mutants"]
            
        logger.info(f"Mutation testing completed: {results['mutation_score']:.2%} mutation score")
        return results
        
    def _test_python(self, repo_path: str, repo_spec: RepoSpec) -> Dict[str, Any]:
        """
        Run mutation testing on Python code.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            Dictionary with mutation testing results
        """
        results = {
            "mutation_score": 0.0,
            "total_mutants": 0,
            "killed_mutants": 0,
            "survived_mutants": 0,
            "timeout_mutants": 0,
            "findings": []
        }
        
        try:
            # Check if mutmut is available
            cmd = ["mutmut", "--version"]
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.info("mutmut not available, skipping Python mutation testing")
                return results
                
            # Run mutation testing
            logger.info("Running Python mutation testing with mutmut")
            start_time = time.time()
            
            cmd = ["mutmut", "run", "--paths-to-mutate", "."]
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            duration = time.time() - start_time
            
            # Get results
            cmd = ["mutmut", "results"]
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse results
            lines = result.stdout.split("\n")
            for line in lines:
                if line.startswith("To kill a mutant"):
                    # Extract statistics
                    parts = line.split()
                    if len(parts) >= 10:
                        results["total_mutants"] = int(parts[4])
                        results["killed_mutants"] = int(parts[6])
                        results["timeout_mutants"] = int(parts[8])
                        results["survived_mutants"] = results["total_mutants"] - results["killed_mutants"] - results["timeout_mutants"]
                        
                        # Calculate mutation score
                        if results["total_mutants"] > 0:
                            results["mutation_score"] = results["killed_mutants"] / results["total_mutants"]
                        break
                        
            # Create findings for survived mutants
            if results["survived_mutants"] > 0:
                # Get detailed results
                cmd = ["mutmut", "show", "all"]
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse detailed results
                lines = result.stdout.split("\n")
                current_file = None
                
                for line in lines:
                    if line.startswith("#"):
                        # Extract file path
                        current_file = line[1:].strip()
                    elif line.startswith("- "):
                        # Extract mutant details
                        mutant_parts = line[2:].split(":")
                        if len(mutant_parts) >= 2:
                            mutant_type = mutant_parts[0].strip()
                            line_number = mutant_parts[1].strip()
                            
                            # Create finding for the survived mutant
                            finding = Finding(
                                repo_id=repo_spec.id,
                                type=FindingType.BUG,
                                severity=Severity.MEDIUM,
                                title=f"Survived mutant: {mutant_type}",
                                description=f"A mutant of type '{mutant_type}' survived testing, indicating a potential gap in test coverage",
                                file_path=current_file,
                                start_line=int(line_number) if line_number.isdigit() else None,
                                metadata={
                                    "tool": "mutmut",
                                    "mutant_type": mutant_type,
                                    "line_number": line_number,
                                }
                            )
                            results["findings"].append(finding)
                            
            # Create a summary finding
            if results["mutation_score"] < 0.8:
                finding = Finding(
                    repo_id=repo_spec.id,
                    type=FindingType.BUG,
                    severity=Severity.MEDIUM if results["mutation_score"] > 0.5 else Severity.HIGH,
                    title="Low mutation testing score",
                    description=f"The mutation testing score is {results['mutation_score']:.2%}, which indicates potential gaps in test coverage",
                    metadata={
                        "tool": "mutmut",
                        "mutation_score": results["mutation_score"],
                        "total_mutants": results["total_mutants"],
                        "killed_mutants": results["killed_mutants"],
                        "survived_mutants": results["survived_mutants"],
                        "timeout_mutants": results["timeout_mutants"],
                        "duration_seconds": duration,
                    }
                )
                results["findings"].append(finding)
                
        except subprocess.TimeoutExpired:
            logger.error("Python mutation testing timed out")
            finding = Finding(
                repo_id=repo_spec.id,
                type=FindingType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Mutation testing timed out",
                description="Python mutation testing took too long to execute",
                metadata={
                    "tool": "mutmut",
                    "timeout_seconds": 600,
                }
            )
            results["findings"].append(finding)
        except Exception as e:
            logger.error(f"Error running Python mutation testing: {e}")
            
        return results
