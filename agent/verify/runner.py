"""
Runner for tests, benchmarks, and verification tasks.
"""

import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agent.core.models import BenchmarkPlan, RiskReport, Severity, TestPlan


def run_tests(test_plan: TestPlan, repo_path: str) -> Dict[str, Any]:
    """
    Run tests according to a test plan.
    
    Args:
        test_plan: Test plan to execute
        repo_path: Path to the repository
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Running {test_plan.test_type} tests")
    
    results = {
        "passed": False,
        "output": "",
        "coverage_percentage": 0.0,
        "execution_time": 0,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        # Run each test command
        all_passed = True
        combined_output = []
        
        for command in test_plan.test_commands:
            logger.debug(f"Running test command: {command}")
            
            # Prepare command
            if isinstance(command, str):
                cmd = command.split()
            else:
                cmd = command
                
            # Run command
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # Collect output
            combined_output.append(f"Command: {' '.join(cmd)}")
            combined_output.append("STDOUT:")
            combined_output.append(result.stdout)
            combined_output.append("STDERR:")
            combined_output.append(result.stderr)
            combined_output.append("-" * 50)
            
            # Check if command succeeded
            if result.returncode != 0:
                all_passed = False
                
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Parse output for coverage information
        coverage_percentage = _parse_coverage_from_output("\n".join(combined_output))
        
        # Update results
        results["passed"] = all_passed
        results["output"] = "\n".join(combined_output)
        results["coverage_percentage"] = coverage_percentage
        results["execution_time"] = execution_time
        
        logger.info(f"Tests {'passed' if all_passed else 'failed'} in {execution_time:.2f}s")
        
    except subprocess.TimeoutExpired:
        error_msg = "Test execution timed out"
        logger.error(error_msg)
        results["error"] = error_msg
    except Exception as e:
        error_msg = f"Error running tests: {e}"
        logger.error(error_msg)
        results["error"] = error_msg
        
    return results


def run_benchmarks(benchmark_plan: BenchmarkPlan, repo_path: str) -> Dict[str, Any]:
    """
    Run benchmarks according to a benchmark plan.
    
    Args:
        benchmark_plan: Benchmark plan to execute
        repo_path: Path to the repository
        
    Returns:
        Dictionary with benchmark results
    """
    logger.info(f"Running {benchmark_plan.benchmark_type} benchmarks")
    
    results = {
        "metrics": {},
        "execution_time": 0,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        # Run each benchmark command
        all_metrics = {}
        combined_output = []
        
        for command in benchmark_plan.benchmark_commands:
            logger.debug(f"Running benchmark command: {command}")
            
            # Prepare command
            if isinstance(command, str):
                cmd = command.split()
            else:
                cmd = command
                
            # Run command
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            # Collect output
            combined_output.append(f"Command: {' '.join(cmd)}")
            combined_output.append("STDOUT:")
            combined_output.append(result.stdout)
            combined_output.append("STDERR:")
            combined_output.append(result.stderr)
            combined_output.append("-" * 50)
            
            # Parse metrics from output
            metrics = _parse_metrics_from_output(result.stdout, benchmark_plan.metrics)
            all_metrics.update(metrics)
            
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update results
        results["metrics"] = all_metrics
        results["execution_time"] = execution_time
        
        logger.info(f"Benchmarks completed in {execution_time:.2f}s")
        
    except subprocess.TimeoutExpired:
        error_msg = "Benchmark execution timed out"
        logger.error(error_msg)
        results["error"] = error_msg
    except Exception as e:
        error_msg = f"Error running benchmarks: {e}"
        logger.error(error_msg)
        results["error"] = error_msg
        
    return results


def verify_changes(
    repo_path: str,
    test_results: Dict[str, Any],
    benchmark_results: Optional[Dict[str, Any]] = None,
    baseline_benchmark_results: Optional[Dict[str, Any]] = None
) -> RiskReport:
    """
    Verify changes by analyzing test and benchmark results.
    
    Args:
        repo_path: Path to the repository
        test_results: Results from running tests
        benchmark_results: Results from running benchmarks
        baseline_benchmark_results: Baseline benchmark results for comparison
        
    Returns:
        Risk report with verification results
    """
    logger.info("Verifying changes")
    
    # Assess overall risk level
    risk_level = _assess_overall_risk(test_results, benchmark_results)
    
    # Identify risk factors
    risk_factors = []
    
    if not test_results.get("passed", False):
        risk_factors.append({
            "type": "test_failure",
            "description": "Tests failed after applying changes",
            "severity": "high"
        })
        
    if test_results.get("coverage_percentage", 0) < 80:
        risk_factors.append({
            "type": "low_coverage",
            "description": f"Test coverage is low: {test_results.get('coverage_percentage', 0)}%",
            "severity": "medium"
        })
        
    if benchmark_results and baseline_benchmark_results:
        # Compare benchmark results
        performance_regression = _check_performance_regression(
            benchmark_results.get("metrics", {}),
            baseline_benchmark_results.get("metrics", {})
        )
        
        if performance_regression:
            risk_factors.append({
                "type": "performance_regression",
                "description": f"Performance regression detected: {performance_regression}",
                "severity": "medium"
            })
            
    # Generate mitigations
    mitigations = []
    
    for factor in risk_factors:
        factor_type = factor.get("type")
        
        if factor_type == "test_failure":
            mitigations.append({
                "type": "fix_tests",
                "description": "Fix failing tests before merging changes"
            })
        elif factor_type == "low_coverage":
            mitigations.append({
                "type": "add_tests",
                "description": "Add tests to improve coverage"
            })
        elif factor_type == "performance_regression":
            mitigations.append({
                "type": "optimize_performance",
                "description": "Optimize code to address performance regression"
            })
            
    # Create risk report
    risk_report = RiskReport(
        repo_id="",  # This would be set by the caller
        patch_id="",  # This would be set by the caller
        overall_risk_level=risk_level,
        risk_factors=risk_factors,
        mitigations=mitigations,
        test_results=test_results,
        benchmark_results=benchmark_results,
        static_analysis_results=None  # This would be populated by the caller
    )
    
    logger.info(f"Verification complete. Overall risk level: {risk_level.value}")
    return risk_report


def _parse_coverage_from_output(output: str) -> float:
    """
    Parse coverage percentage from test output.
    
    Args:
        output: Test output
        
    Returns:
        Coverage percentage
    """
    # Look for common coverage patterns
    import re
    
    patterns = [
        r"Coverage:\s*(\d+(?:\.\d+)?)%",
        r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%",
        r"line coverage:\s*(\d+(?:\.\d+)?)%",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
                
    return 0.0


def _parse_metrics_from_output(output: str, expected_metrics: List[str]) -> Dict[str, Any]:
    """
    Parse metrics from benchmark output.
    
    Args:
        output: Benchmark output
        expected_metrics: List of expected metric names
        
    Returns:
        Dictionary with parsed metrics
    """
    metrics = {}
    
    # Look for common metric patterns
    import re
    
    for metric in expected_metrics:
        # Try different patterns for the metric
        patterns = [
            rf"{metric}:\s*(\d+(?:\.\d+)?)",
            rf"{metric}\s*=\s*(\d+(?:\.\d+)?)",
            rf'"{metric}":\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    # Try to parse as float first
                    value = float(match.group(1))
                    metrics[metric] = value
                    break
                except ValueError:
                    continue
                    
    return metrics


def _assess_overall_risk(
    test_results: Dict[str, Any],
    benchmark_results: Optional[Dict[str, Any]] = None
) -> Severity:
    """
    Assess the overall risk level based on test and benchmark results.
    
    Args:
        test_results: Results from running tests
        benchmark_results: Results from running benchmarks
        
    Returns:
        Overall risk level
    """
    # Start with low risk
    risk_level = Severity.LOW
    
    # Check test results
    if not test_results.get("passed", False):
        # Test failures are high risk
        risk_level = Severity.HIGH
    elif test_results.get("coverage_percentage", 0) < 50:
        # Very low coverage is medium risk
        risk_level = Severity.MEDIUM
        
    # Check benchmark results
    if benchmark_results:
        # If there are benchmark results but no baseline, we can't assess risk
        pass
        
    return risk_level


def _check_performance_regression(
    current_metrics: Dict[str, Any],
    baseline_metrics: Dict[str, Any],
    threshold: float = 0.1
) -> Optional[str]:
    """
    Check for performance regression by comparing current and baseline metrics.
    
    Args:
        current_metrics: Current benchmark metrics
        baseline_metrics: Baseline benchmark metrics
        threshold: Regression threshold (10% by default)
        
    Returns:
        Description of the regression if found, None otherwise
    """
    regressions = []
    
    for metric, current_value in current_metrics.items():
        if metric in baseline_metrics:
            baseline_value = baseline_metrics[metric]
            
            # Calculate percentage change
            if baseline_value > 0:
                change = (current_value - baseline_value) / baseline_value
                
                # Check if this is a regression (increase in time/memory, decrease in throughput)
                is_regression = False
                
                if metric.endswith("_time") or metric.endswith("_ms") or metric.endswith("_seconds"):
                    # Time metrics - lower is better
                    is_regression = change > threshold
                elif metric.endswith("_throughput") or metric.endswith("_rate"):
                    # Throughput metrics - higher is better
                    is_regression = change < -threshold
                elif metric.endswith("_memory") or metric.endswith("_bytes"):
                    # Memory metrics - lower is better
                    is_regression = change > threshold
                    
                if is_regression:
                    regressions.append(
                        f"{metric}: {baseline_value} -> {current_value} ({change:.1%})"
                    )
                    
    if regressions:
        return "; ".join(regressions)
        
    return None
