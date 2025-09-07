"""
Dynamic analysis pipeline for runtime behavior and performance.
"""

import json
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agent.core.models import Finding, FindingType, Language, RepoSpec, Severity


class DynamicAnalysisPipeline:
    """
    Pipeline for dynamic code analysis.
    """
    
    def __init__(self):
        """Initialize the dynamic analysis pipeline."""
        self.supported_languages = [Language.PYTHON, Language.TYPESCRIPT]
        
    def analyze(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run dynamic analysis on a repository.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        # Run language-specific analysis
        for language in repo_spec.languages or self.supported_languages:
            if language == Language.PYTHON:
                findings.extend(self._analyze_python(repo_path, repo_spec))
            elif language == Language.TYPESCRIPT:
                findings.extend(self._analyze_typescript(repo_path, repo_spec))
                
        logger.info(f"Found {len(findings)} issues through dynamic analysis")
        return findings
        
    def _analyze_python(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run dynamic analysis on Python code.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        # Run tests to check for runtime errors
        findings.extend(self._run_python_tests(repo_path, repo_spec))
        
        # Check for performance issues
        findings.extend(self._run_python_profiling(repo_path, repo_spec))
        
        return findings
        
    def _analyze_typescript(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run dynamic analysis on TypeScript code.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        # Run tests to check for runtime errors
        findings.extend(self._run_typescript_tests(repo_path, repo_spec))
        
        return findings
        
    def _run_python_tests(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run Python tests to check for runtime errors.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Check if pytest is available
            cmd = ["python", "-m", "pytest", "--version"]
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.info("pytest not available, skipping Python test analysis")
                return findings
                
            # Prepare command
            cmd = ["python", "-m", "pytest", "--tb=short", "-v"]
            
            # Run tests
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            duration = time.time() - start_time
            
            # Parse output for failures
            if result.returncode != 0:
                # Extract test failures
                lines = result.stdout.split("\n")
                current_test = None
                
                for line in lines:
                    if line.startswith("FAILED "):
                        # Extract test name
                        parts = line.split()
                        if len(parts) >= 2:
                            current_test = parts[1]
                            
                        # Create finding for the failed test
                        finding = Finding(
                            repo_id=repo_spec.id,
                            type=FindingType.BUG,
                            severity=Severity.HIGH,
                            title=f"Test failed: {current_test}",
                            description=f"Test {current_test} failed during execution",
                            metadata={
                                "tool": "pytest",
                                "test_name": current_test,
                                "duration_seconds": duration,
                                "output": result.stdout,
                            }
                        )
                        findings.append(finding)
                        
        except subprocess.TimeoutExpired:
            logger.error("Python test execution timed out")
            finding = Finding(
                repo_id=repo_spec.id,
                type=FindingType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Test execution timed out",
                description="Python tests took too long to execute",
                metadata={
                    "tool": "pytest",
                    "timeout_seconds": 300,
                }
            )
            findings.append(finding)
        except Exception as e:
            logger.error(f"Error running Python tests: {e}")
            
        return findings
        
    def _run_python_profiling(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run Python profiling to check for performance issues.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Look for performance bottlenecks in the code
            # This is a simplified implementation that looks for common performance issues
            
            # Check for inefficient patterns in Python files
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, repo_path)
                        
                        # Skip test files
                        if "test" in rel_path:
                            continue
                            
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        # Check for inefficient patterns
                        if "import *" in content:
                            finding = Finding(
                                repo_id=repo_spec.id,
                                type=FindingType.PERFORMANCE,
                                severity=Severity.LOW,
                                title="Inefficient import pattern",
                                description="Using 'import *' can lead to performance issues and makes code harder to understand",
                                file_path=rel_path,
                                metadata={
                                    "tool": "pattern_matching",
                                    "pattern": "import *",
                                }
                            )
                            findings.append(finding)
                            
                        # Check for potential memory leaks
                        if "global " in content and "list" in content:
                            finding = Finding(
                                repo_id=repo_spec.id,
                                type=FindingType.PERFORMANCE,
                                severity=Severity.MEDIUM,
                                title="Potential memory leak",
                                description="Global lists can lead to memory leaks if not properly managed",
                                file_path=rel_path,
                                metadata={
                                    "tool": "pattern_matching",
                                    "pattern": "global list",
                                }
                            )
                            findings.append(finding)
                            
        except Exception as e:
            logger.error(f"Error running Python profiling: {e}")
            
        return findings
        
    def _run_typescript_tests(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run TypeScript tests to check for runtime errors.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Check if package.json exists
            package_json_path = os.path.join(repo_path, "package.json")
            if not os.path.exists(package_json_path):
                logger.info("No package.json found, skipping TypeScript test analysis")
                return findings
                
            # Check if test scripts are defined
            with open(package_json_path, "r") as f:
                package_json = json.load(f)
                
            scripts = package_json.get("scripts", {})
            test_script = None
            
            for script_name in ["test", "test:unit", "test:integration"]:
                if script_name in scripts:
                    test_script = scripts[script_name]
                    break
                    
            if not test_script:
                logger.info("No test script found in package.json, skipping TypeScript test analysis")
                return findings
                
            # Prepare command
            cmd = ["npm", "run", test_script.split()[0]]
            
            # Run tests
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            duration = time.time() - start_time
            
            # Parse output for failures
            if result.returncode != 0:
                # Extract test failures
                lines = result.stdout.split("\n")
                current_test = None
                
                for line in lines:
                    if "✕" in line or "FAIL" in line:
                        # Extract test name
                        parts = line.split()
                        if len(parts) >= 2:
                            current_test = " ".join(parts[1:])
                            
                        # Create finding for the failed test
                        finding = Finding(
                            repo_id=repo_spec.id,
                            type=FindingType.BUG,
                            severity=Severity.HIGH,
                            title=f"Test failed: {current_test}",
                            description=f"Test {current_test} failed during execution",
                            metadata={
                                "tool": "npm_test",
                                "test_name": current_test,
                                "duration_seconds": duration,
                                "output": result.stdout,
                            }
                        )
                        findings.append(finding)
                        
        except subprocess.TimeoutExpired:
            logger.error("TypeScript test execution timed out")
            finding = Finding(
                repo_id=repo_spec.id,
                type=FindingType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Test execution timed out",
                description="TypeScript tests took too long to execute",
                metadata={
                    "tool": "npm_test",
                    "timeout_seconds": 300,
                }
            )
            findings.append(finding)
        except Exception as e:
            logger.error(f"Error running TypeScript tests: {e}")
            
        return findings
