"""
Tests for static analysis pipeline functionality.
"""

import unittest
from unittest.mock import patch, MagicMock

from agent.analysis.static_pipeline import StaticAnalysisPipeline
from agent.core.models import Finding, FindingType, Severity, Language, RepoSpec


class TestStaticAnalysisPipeline(unittest.TestCase):
    """Test cases for static analysis pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = StaticAnalysisPipeline()
        self.repo_spec = RepoSpec(
            id="test-repo-id",
            url="https://github.com/example/repo.git",
            languages=[Language.PYTHON]
        )

    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._analyze_python')
    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._analyze_typescript')
    def test_analyze(self, mock_analyze_ts, mock_analyze_py):
        """Test running static analysis."""
        # Setup mocks
        mock_analyze_py.return_value = [
            Finding(
                id="finding-1",
                repo_id="test-repo-id",
                type=FindingType.SECURITY,
                severity=Severity.HIGH,
                title="Security Issue",
                description="A security vulnerability was found"
            )
        ]
        
        mock_analyze_ts.return_value = [
            Finding(
                id="finding-2",
                repo_id="test-repo-id",
                type=FindingType.STYLE,
                severity=Severity.LOW,
                title="Style Issue",
                description="A style issue was found"
            )
        ]
        
        # Call function
        findings = self.pipeline.analyze("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 2)
        mock_analyze_py.assert_called_once_with("/tmp/repo", self.repo_spec)
        mock_analyze_ts.assert_called_once_with("/tmp/repo", self.repo_spec)

    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._run_ruff')
    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._run_bandit')
    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._run_safety')
    def test_analyze_python(self, mock_run_safety, mock_run_bandit, mock_run_ruff):
        """Test analyzing Python code."""
        # Setup mocks
        mock_run_ruff.return_value = [
            Finding(
                id="ruff-finding",
                repo_id="test-repo-id",
                type=FindingType.STYLE,
                severity=Severity.MEDIUM,
                title="Style Issue",
                description="A style issue was found by ruff"
            )
        ]
        
        mock_run_bandit.return_value = [
            Finding(
                id="bandit-finding",
                repo_id="test-repo-id",
                type=FindingType.SECURITY,
                severity=Severity.HIGH,
                title="Security Issue",
                description="A security issue was found by bandit"
            )
        ]
        
        mock_run_safety.return_value = [
            Finding(
                id="safety-finding",
                repo_id="test-repo-id",
                type=FindingType.SECURITY,
                severity=Severity.HIGH,
                title="Vulnerable Dependency",
                description="A vulnerable dependency was found"
            )
        ]
        
        # Call function
        findings = self.pipeline._analyze_python("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 3)
        mock_run_ruff.assert_called_once_with("/tmp/repo", self.repo_spec)
        mock_run_bandit.assert_called_once_with("/tmp/repo", self.repo_spec)
        mock_run_safety.assert_called_once_with("/tmp/repo", self.repo_spec)

    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._run_eslint')
    @patch('agent.analysis.static_pipeline.StaticAnalysisPipeline._run_npm_audit')
    def test_analyze_typescript(self, mock_run_npm_audit, mock_run_eslint):
        """Test analyzing TypeScript code."""
        # Setup mocks
        mock_run_eslint.return_value = [
            Finding(
                id="eslint-finding",
                repo_id="test-repo-id",
                type=FindingType.STYLE,
                severity=Severity.MEDIUM,
                title="Style Issue",
                description="A style issue was found by ESLint"
            )
        ]
        
        mock_run_npm_audit.return_value = [
            Finding(
                id="npm-audit-finding",
                repo_id="test-repo-id",
                type=FindingType.SECURITY,
                severity=Severity.HIGH,
                title="Vulnerable Dependency",
                description="A vulnerable dependency was found by npm audit"
            )
        ]
        
        # Call function
        findings = self.pipeline._analyze_typescript("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 2)
        mock_run_eslint.assert_called_once_with("/tmp/repo", self.repo_spec)
        mock_run_npm_audit.assert_called_once_with("/tmp/repo", self.repo_spec)

    @patch('subprocess.run')
    def test_run_ruff(self, mock_run):
        """Test running ruff."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = '''
        [
            {
                "filename": "/tmp/repo/src/main.py",
                "location": {"row": 10, "column": 5},
                "end_location": {"row": 10, "column": 10},
                "code": "E401",
                "message": "Multiple imports on one line",
                "url": "https://beta.ruff.rs/docs/rules/multiple-imports-on-one-line"
            }
        ]
        '''
        mock_run.return_value = mock_result
        
        # Call function
        findings = self.pipeline._run_ruff("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].type, FindingType.STYLE)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].title, "Multiple imports on one line")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_bandit(self, mock_run):
        """Test running bandit."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = '''
        {
            "results": [
                {
                    "test_id": "B608",
                    "issue_text": "Possible SQL injection vector through string-based query construction.",
                    "issue_severity": "HIGH",
                    "filename": "/tmp/repo/src/database.py",
                    "line_number": 42,
                    "issue_cwe": {
                        "id": 89,
                        "link": "https://cwe.mitre.org/data/definitions/89.html"
                    }
                }
            ]
        }
        '''
        mock_run.return_value = mock_result
        
        # Call function
        findings = self.pipeline._run_bandit("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].type, FindingType.SECURITY)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].title, "Possible SQL injection vector through string-based query construction.")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_safety(self, mock_run):
        """Test running safety."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = '''
        [
            {
                "id": "12345",
                "package": "requests",
                "installed_version": "2.20.0",
                "vulnerable_version": "<2.25.0",
                "advisory": "A vulnerability in requests allows for CRLF injection",
                "cvss_score": 5.9
            }
        ]
        '''
        mock_run.return_value = mock_result
        
        # Call function
        findings = self.pipeline._run_safety("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].type, FindingType.SECURITY)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].title, "Vulnerable dependency: requests")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_eslint(self, mock_run):
        """Test running ESLint."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = '''
        [
            {
                "filePath": "/tmp/repo/src/app.ts",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "message": "'x' is assigned a value but never used.",
                        "line": 5,
                        "column": 5,
                        "endLine": 5,
                        "endColumn": 6,
                        "nodeType": "Identifier"
                    }
                ]
            }
        ]
        '''
        mock_run.return_value = mock_result
        
        # Call function
        findings = self.pipeline._run_eslint("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].type, FindingType.STYLE)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].title, "'x' is assigned a value but never used.")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_npm_audit(self, mock_run):
        """Test running npm audit."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = '''
        {
            "vulnerabilities": {
                "lodash": {
                    "name": "lodash",
                    "severity": "high",
                    "isDirect": true,
                    "via": [
                        {
                            "id": "12345",
                            "title": "Prototype Pollution",
                            "url": "https://npmjs.com/advisories/12345"
                        }
                    ]
                }
            }
        }
        '''
        mock_run.return_value = mock_result
        
        # Call function
        findings = self.pipeline._run_npm_audit("/tmp/repo", self.repo_spec)
        
        # Assertions
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].type, FindingType.SECURITY)
        self.assertEqual(findings[0].severity, Severity.HIGH)
        self.assertEqual(findings[0].title, "Vulnerable dependency: lodash")
        mock_run.assert_called_once()

    def test_ruff_code_to_severity(self):
        """Test converting ruff error codes to severity levels."""
        self.assertEqual(self.pipeline._ruff_code_to_severity("E401"), Severity.HIGH)
        self.assertEqual(self.pipeline._ruff_code_to_severity("W503"), Severity.MEDIUM)
        self.assertEqual(self.pipeline._ruff_code_to_severity("F401"), Severity.HIGH)
        self.assertEqual(self.pipeline._ruff_code_to_severity("C901"), Severity.MEDIUM)
        self.assertEqual(self.pipeline._ruff_code_to_severity("N802"), Severity.LOW)
        self.assertEqual(self.pipeline._ruff_code_to_severity("UP007"), Severity.LOW)
        self.assertEqual(self.pipeline._ruff_code_to_severity("B006"), Severity.HIGH)
        self.assertEqual(self.pipeline._ruff_code_to_severity("UNKNOWN"), Severity.MEDIUM)

    def test_bandit_severity_to_severity(self):
        """Test converting bandit severity levels to severity enums."""
        self.assertEqual(self.pipeline._bandit_severity_to_severity("HIGH"), Severity.HIGH)
        self.assertEqual(self.pipeline._bandit_severity_to_severity("MEDIUM"), Severity.MEDIUM)
        self.assertEqual(self.pipeline._bandit_severity_to_severity("LOW"), Severity.LOW)
        self.assertEqual(self.pipeline._bandit_severity_to_severity("UNKNOWN"), Severity.MEDIUM)

    def test_eslint_severity_to_severity(self):
        """Test converting ESLint severity levels to severity enums."""
        self.assertEqual(self.pipeline._eslint_severity_to_severity(2), Severity.HIGH)
        self.assertEqual(self.pipeline._eslint_severity_to_severity(1), Severity.MEDIUM)
        self.assertEqual(self.pipeline._eslint_severity_to_severity(0), Severity.MEDIUM)

    def test_npm_severity_to_severity(self):
        """Test converting npm audit severity levels to severity enums."""
        self.assertEqual(self.pipeline._npm_severity_to_severity("critical"), Severity.CRITICAL)
        self.assertEqual(self.pipeline._npm_severity_to_severity("high"), Severity.HIGH)
        self.assertEqual(self.pipeline._npm_severity_to_severity("moderate"), Severity.MEDIUM)
        self.assertEqual(self.pipeline._npm_severity_to_severity("low"), Severity.LOW)
        self.assertEqual(self.pipeline._npm_severity_to_severity("unknown"), Severity.MEDIUM)


if __name__ == "__main__":
    unittest.main()
