"""
Static analysis pipeline for code quality and security issues.
"""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agent.core.models import Finding, FindingType, Language, RepoSpec, Severity


class StaticAnalysisPipeline:
    """
    Pipeline for static code analysis.
    """
    
    def __init__(self):
        """Initialize the static analysis pipeline."""
        self.supported_languages = [Language.PYTHON, Language.TYPESCRIPT]
        
    def analyze(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run static analysis on a repository.
        
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
                
        logger.info(f"Found {len(findings)} issues through static analysis")
        return findings
        
    def _analyze_python(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run static analysis on Python code.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        # Run ruff for linting and style issues
        findings.extend(self._run_ruff(repo_path, repo_spec))
        
        # Run bandit for security issues
        findings.extend(self._run_bandit(repo_path, repo_spec))
        
        # Run safety for dependency security issues
        findings.extend(self._run_safety(repo_path, repo_spec))
        
        return findings
        
    def _analyze_typescript(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run static analysis on TypeScript code.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        # Run ESLint for linting and style issues
        findings.extend(self._run_eslint(repo_path, repo_spec))
        
        # Run npm audit for dependency security issues
        findings.extend(self._run_npm_audit(repo_path, repo_spec))
        
        return findings
        
    def _run_ruff(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run ruff for Python linting.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Prepare command
            cmd = ["ruff", "check", "--format=json", repo_path]
            
            # Run ruff
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # No issues found
                return findings
                
            # Parse JSON output
            try:
                ruff_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse ruff output: {result.stdout}")
                return findings
                
            # Convert ruff results to findings
            for ruff_result in ruff_results:
                finding = Finding(
                    repo_id=repo_spec.id,
                    type=FindingType.STYLE,
                    severity=self._ruff_code_to_severity(ruff_result.get("code", "")),
                    title=ruff_result.get("message", ""),
                    description=ruff_result.get("message", ""),
                    file_path=ruff_result.get("filename", ""),
                    start_line=ruff_result.get("location", {}).get("row"),
                    end_line=ruff_result.get("end_location", {}).get("row"),
                    start_column=ruff_result.get("location", {}).get("column"),
                    end_column=ruff_result.get("end_location", {}).get("column"),
                    rule_id=ruff_result.get("code"),
                    metadata={
                        "tool": "ruff",
                        "code": ruff_result.get("code"),
                        "url": ruff_result.get("url"),
                    }
                )
                findings.append(finding)
                
        except subprocess.TimeoutExpired:
            logger.error("Ruff analysis timed out")
        except Exception as e:
            logger.error(f"Error running ruff: {e}")
            
        return findings
        
    def _run_bandit(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run bandit for Python security analysis.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Prepare command
            cmd = ["bandit", "-r", "-f", "json", repo_path]
            
            # Run bandit
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse JSON output
            try:
                bandit_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse bandit output: {result.stdout}")
                return findings
                
            # Convert bandit results to findings
            for bandit_result in bandit_results.get("results", []):
                finding = Finding(
                    repo_id=repo_spec.id,
                    type=FindingType.SECURITY,
                    severity=self._bandit_severity_to_severity(bandit_result.get("issue_severity", "")),
                    title=bandit_result.get("issue_text", ""),
                    description=bandit_result.get("issue_text", ""),
                    file_path=bandit_result.get("filename", ""),
                    start_line=bandit_result.get("line_number"),
                    rule_id=bandit_result.get("test_id"),
                    metadata={
                        "tool": "bandit",
                        "test_id": bandit_result.get("test_id"),
                        "issue_cwe": bandit_result.get("issue_cwe"),
                    }
                )
                findings.append(finding)
                
        except subprocess.TimeoutExpired:
            logger.error("Bandit analysis timed out")
        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            
        return findings
        
    def _run_safety(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run safety for Python dependency security analysis.
        
        Args:
            repo_path: Path to the repository
            repo_spec: Repository specification
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Check if requirements files exist
            requirements_files = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.startswith("requirements") and file.endswith(".txt"):
                        requirements_files.append(os.path.join(root, file))
                        
            if not requirements_files:
                logger.info("No requirements files found, skipping safety analysis")
                return findings
                
            # Run safety for each requirements file
            for req_file in requirements_files:
                cmd = ["safety", "check", "--file", req_file, "--json"]
                
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Parse JSON output
                try:
                    safety_results = json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse safety output: {result.stdout}")
                    continue
                    
                # Convert safety results to findings
                for safety_result in safety_results:
                    finding = Finding(
                        repo_id=repo_spec.id,
                        type=FindingType.SECURITY,
                        severity=Severity.HIGH,  # Dependency vulnerabilities are usually high severity
                        title=f"Vulnerable dependency: {safety_result.get('package', '')}",
                        description=safety_result.get("advisory", ""),
                        file_path=req_file,
                        rule_id=safety_result.get("id"),
                        metadata={
                            "tool": "safety",
                            "package": safety_result.get("package"),
                            "installed_version": safety_result.get("installed_version"),
                            "vulnerable_version": safety_result.get("vulnerable_version"),
                            "cvss_score": safety_result.get("cvss_score"),
                        }
                    )
                    findings.append(finding)
                    
        except subprocess.TimeoutExpired:
            logger.error("Safety analysis timed out")
        except Exception as e:
            logger.error(f"Error running safety: {e}")
            
        return findings
        
    def _run_eslint(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run ESLint for TypeScript/JavaScript linting.
        
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
                logger.info("No package.json found, skipping ESLint analysis")
                return findings
                
            # Check if ESLint is installed
            cmd = ["npx", "eslint", "--version"]
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.info("ESLint not installed, skipping ESLint analysis")
                return findings
                
            # Prepare command
            cmd = ["npx", "eslint", "--format=json", repo_path]
            
            # Run ESLint
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # No issues found
                return findings
                
            # Parse JSON output
            try:
                eslint_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse ESLint output: {result.stdout}")
                return findings
                
            # Convert ESLint results to findings
            for file_result in eslint_results:
                file_path = file_result.get("filePath", "")
                messages = file_result.get("messages", [])
                
                for message in messages:
                    finding = Finding(
                        repo_id=repo_spec.id,
                        type=FindingType.STYLE,
                        severity=self._eslint_severity_to_severity(message.get("severity", 0)),
                        title=message.get("message", ""),
                        description=message.get("message", ""),
                        file_path=file_path,
                        start_line=message.get("line"),
                        end_line=message.get("endLine"),
                        start_column=message.get("column"),
                        end_column=message.get("endColumn"),
                        rule_id=message.get("ruleId"),
                        metadata={
                            "tool": "eslint",
                            "ruleId": message.get("ruleId"),
                            "nodeType": message.get("nodeType"),
                        }
                    )
                    findings.append(finding)
                    
        except subprocess.TimeoutExpired:
            logger.error("ESLint analysis timed out")
        except Exception as e:
            logger.error(f"Error running ESLint: {e}")
            
        return findings
        
    def _run_npm_audit(self, repo_path: str, repo_spec: RepoSpec) -> List[Finding]:
        """
        Run npm audit for TypeScript/JavaScript dependency security analysis.
        
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
                logger.info("No package.json found, skipping npm audit")
                return findings
                
            # Prepare command
            cmd = ["npm", "audit", "--json"]
            
            # Run npm audit
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse JSON output
            try:
                audit_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse npm audit output: {result.stdout}")
                return findings
                
            # Convert npm audit results to findings
            vulnerabilities = audit_results.get("vulnerabilities", {})
            for package_name, vuln_info in vulnerabilities.items():
                finding = Finding(
                    repo_id=repo_spec.id,
                    type=FindingType.SECURITY,
                    severity=self._npm_severity_to_severity(vuln_info.get("severity", "")),
                    title=f"Vulnerable dependency: {package_name}",
                    description=vuln_info.get("title", ""),
                    file_path=package_json_path,
                    rule_id=vuln_info.get("id"),
                    metadata={
                        "tool": "npm_audit",
                        "package": package_name,
                        "version": vuln_info.get("version"),
                        "range": vuln_info.get("range"),
                        "vulnerable_versions": vuln_info.get("vulnerable_versions"),
                        "cve": vuln_info.get("cve"),
                    }
                )
                findings.append(finding)
                
        except subprocess.TimeoutExpired:
            logger.error("npm audit timed out")
        except Exception as e:
            logger.error(f"Error running npm audit: {e}")
            
        return findings
        
    def _ruff_code_to_severity(self, code: str) -> Severity:
        """
        Convert a ruff error code to a severity level.
        
        Args:
            code: Ruff error code
            
        Returns:
            Severity level
        """
        if not code:
            return Severity.MEDIUM
            
        # Ruff error codes start with a letter indicating the category
        category = code[0]
        
        if category == "E":
            # Error
            return Severity.HIGH
        elif category == "W":
            # Warning
            return Severity.MEDIUM
        elif category == "F":
            # Pyflakes (usually serious)
            return Severity.HIGH
        elif category == "C":
            # McCabe complexity
            return Severity.MEDIUM
        elif category == "N":
            # Naming conventions
            return Severity.LOW
        elif category == "UP":
            # Pyupgrade
            return Severity.LOW
        elif category == "B":
            # Flake8-bugbear
            return Severity.HIGH
        else:
            return Severity.MEDIUM
            
    def _bandit_severity_to_severity(self, severity: str) -> Severity:
        """
        Convert a bandit severity level to a severity enum.
        
        Args:
            severity: Bandit severity level
            
        Returns:
            Severity enum
        """
        if severity == "HIGH":
            return Severity.HIGH
        elif severity == "MEDIUM":
            return Severity.MEDIUM
        elif severity == "LOW":
            return Severity.LOW
        else:
            return Severity.MEDIUM
            
    def _eslint_severity_to_severity(self, severity: int) -> Severity:
        """
        Convert an ESLint severity level to a severity enum.
        
        Args:
            severity: ESLint severity level (1=warning, 2=error)
            
        Returns:
            Severity enum
        """
        if severity == 2:
            return Severity.HIGH
        else:
            return Severity.MEDIUM
            
    def _npm_severity_to_severity(self, severity: str) -> Severity:
        """
        Convert an npm audit severity level to a severity enum.
        
        Args:
            severity: npm audit severity level
            
        Returns:
            Severity enum
        """
        if severity == "critical":
            return Severity.CRITICAL
        elif severity == "high":
            return Severity.HIGH
        elif severity == "moderate":
            return Severity.MEDIUM
        elif severity == "low":
            return Severity.LOW
        else:
            return Severity.MEDIUM
