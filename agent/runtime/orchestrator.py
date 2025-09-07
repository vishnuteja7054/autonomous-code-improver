"""
Orchestrator for the autonomous code improvement system.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from agent.core.models import Job, JobStatus, RepoSpec
from agent.graph.service import GraphService
from agent.ingestion.clone import clone_repository
from agent.ingestion.indexer import index_repository
from agent.ingestion.parser import parse_file
from agent.analysis.static_pipeline import StaticAnalysisPipeline
from agent.analysis.dynamic_pipeline import DynamicAnalysisPipeline
from agent.analysis.mutation import MutationTester
from agent.llm.client import LLMClient
from agent.brains.innovator import Innovator
from agent.modify.planner import create_refactor_plan
from agent.modify.apply import apply_patch, generate_diff
from agent.verify.runner import run_tests, run_benchmarks, verify_changes
from agent.pr.gh import create_pr, get_pr_status

# Initialize FastAPI app
app = FastAPI(title="Autonomous Code Improver", version="0.1.0")

# Global services
graph_service = None
llm_client = None
static_pipeline = None
dynamic_pipeline = None
mutation_tester = None
innovator = None

# Job storage
jobs = {}


class EnhancementRequest(BaseModel):
    """Request model for code enhancement."""
    repo_url: str
    branch: Optional[str] = None
    commit: Optional[str] = None
    languages: Optional[List[str]] = None
    paths: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    dry_run: bool = False


class EnhancementResponse(BaseModel):
    """Response model for code enhancement."""
    job_id: str
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global graph_service, llm_client, static_pipeline, dynamic_pipeline, mutation_tester, innovator
    
    logger.info("Starting up Autonomous Code Improver")
    
    # Initialize services
    graph_service = GraphService(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )
    graph_service.connect()
    
    llm_client = LLMClient(
        endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1"),
        api_key=os.getenv("LLM_API_KEY"),
        timeout=int(os.getenv("LLM_TIMEOUT", "30"))
    )
    
    static_pipeline = StaticAnalysisPipeline()
    dynamic_pipeline = DynamicAnalysisPipeline()
    mutation_tester = MutationTester()
    innovator = Innovator(llm_client)
    
    logger.info("Services initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    logger.info("Shutting down Autonomous Code Improver")
    
    if graph_service:
        graph_service.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Autonomous Code Improver API"}


@app.post("/enhance", response_model=EnhancementResponse)
async def submit_enhancement_job(request: EnhancementRequest, background_tasks: BackgroundTasks):
    """
    Submit a code enhancement job.
    
    Args:
        request: Enhancement request
        background_tasks: FastAPI background tasks
        
    Returns:
        Enhancement response with job ID
    """
    # Create job
    job_id = str(uuid.uuid4())
    job = Job(
        id=uuid.UUID(job_id),
        job_type="enhancement",
        repo_id=uuid.UUID(job_id),  # Use job ID as repo ID for now
        status=JobStatus.PENDING
    )
    jobs[job_id] = job
    
    # Start enhancement in background
    background_tasks.add_task(run_enhancement, job_id, request)
    
    return EnhancementResponse(
        job_id=job_id,
        status="pending",
        message="Enhancement job submitted"
    )


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a job.
    
    Args:
        job_id: Job ID
        
    Returns:
        Job status
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": job.progress,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "result_data": job.result_data
    }


@app.get("/findings/{repo_id}")
async def get_findings(repo_id: str):
    """
    Get findings for a repository.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        List of findings
    """
    # This is a placeholder implementation
    # In a real implementation, you would query the database for findings
    return {"findings": [], "repo_id": repo_id}


@app.get("/proposals/{repo_id}")
async def get_proposals(repo_id: str):
    """
    Get feature proposals for a repository.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        List of feature proposals
    """
    # This is a placeholder implementation
    # In a real implementation, you would query the database for proposals
    return {"proposals": [], "repo_id": repo_id}


@app.get("/pr/{pr_id}")
async def get_pr_info(pr_id: int):
    """
    Get information about a pull request.
    
    Args:
        pr_id: Pull request ID
        
    Returns:
        Pull request information
    """
    # This is a placeholder implementation
    # In a real implementation, you would query GitHub for PR information
    return {"pr_id": pr_id, "status": "unknown"}


async def run_enhancement(job_id: str, request: EnhancementRequest):
    """
    Run the code enhancement process.
    
    Args:
        job_id: Job ID
        request: Enhancement request
    """
    try:
        # Get job
        job = jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        logger.info(f"Starting enhancement job {job_id}")
        
        # Create repo spec
        repo_spec = RepoSpec(
            id=job.repo_id,
            url=request.repo_url,
            branch=request.branch,
            commit=request.commit,
            languages=request.languages,
            paths=request.paths,
            exclude_patterns=request.exclude_patterns
        )
        
        # Step 1: Clone repository
        update_job_progress(job_id, 0.1, "Cloning repository")
        clone_path, repo = clone_repository(repo_spec)
        
        try:
            # Step 2: Index repository
            update_job_progress(job_id, 0.2, "Indexing repository")
            parse_units = index_repository(clone_path, repo_spec)
            
            # Step 3: Parse files
            update_job_progress(job_id, 0.3, "Parsing files")
            for i, parse_unit in enumerate(parse_units):
                parse_unit = parse_file(parse_unit)
                parse_units[i] = parse_unit
                
                # Store symbols and edges in graph
                for symbol in parse_unit.symbols:
                    graph_service.upsert_symbol(symbol)
                    
                for edge in parse_unit.edges:
                    graph_service.upsert_edge(edge)
                    
                update_job_progress(job_id, 0.3 + (0.1 * i / len(parse_units)), f"Parsing file {i+1}/{len(parse_units)}")
            
            # Step 4: Static analysis
            update_job_progress(job_id, 0.5, "Running static analysis")
            static_findings = static_pipeline.analyze(clone_path, repo_spec)
            
            # Step 5: Dynamic analysis
            update_job_progress(job_id, 0.6, "Running dynamic analysis")
            dynamic_findings = dynamic_pipeline.analyze(clone_path, repo_spec)
            
            # Step 6: Mutation testing
            update_job_progress(job_id, 0.7, "Running mutation testing")
            mutation_results = mutation_tester.test(clone_path, repo_spec)
            
            # Step 7: Generate feature proposals
            update_job_progress(job_id, 0.8, "Generating feature proposals")
            codebase_summary = generate_codebase_summary(parse_units, static_findings, dynamic_findings)
            current_issues = [f.title for f in static_findings + dynamic_findings]
            feature_proposals = innovator.discover_features(clone_path, repo_spec, codebase_summary, current_issues)
            
            # Step 8: Create refactoring plans
            update_job_progress(job_id, 0.9, "Creating refactoring plans")
            refactor_plans = []
            
            # For each finding, create a refactoring plan
            for finding in static_findings[:5]:  # Limit to top 5 findings for demo
                if finding.file_path:
                    # Get the file content
                    file_path = os.path.join(clone_path, finding.file_path)
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8") as f:
                            code = f.read()
                            
                        # Create refactoring plan
                        plan = create_refactor_plan(
                            clone_path,
                            repo_spec,
                            finding.file_path,
                            code,
                            f"Fix {finding.title}",
                            llm_client
                        )
                        
                        if plan:
                            refactor_plans.append(plan)
            
            # Step 9: Apply changes (if not dry run)
            if not request.dry_run and refactor_plans:
                update_job_progress(job_id, 0.95, "Applying changes")
                
                # For each plan, apply the changes
                for plan in refactor_plans[:2]:  # Limit to top 2 plans for demo
                    for change in plan.changes:
                        # This is a simplified implementation
                        # In a real implementation, you would generate actual patches
                        pass
                
                # Create PR if GitHub token is available
                github_token = os.getenv("GITHUB_TOKEN")
                if github_token:
                    # Extract repo owner and name from URL
                    repo_parts = request.repo_url.split("/")
                    repo_owner = repo_parts[-2]
                    repo_name = repo_parts[-1].replace(".git", "")
                    
                    # Create PR summary
                    from agent.core.models import PRSummary
                    pr_summary = PRSummary(
                        repo_id=repo_spec.id,
                        title="Automated Code Improvements",
                        description="This PR contains automated code improvements generated by the Autonomous Code Improver.",
                        patches=[]
                    )
                    
                    # Create PR
                    pr_summary = create_pr(
                        pr_summary,
                        repo_owner,
                        repo_name,
                        "autonomous-improvements",
                        request.branch or "main",
                        github_token
                    )
                    
                    # Store PR info in job result
                    job.result_data["pr_id"] = pr_summary.pr_id
                    job.result_data["pr_url"] = pr_summary.pr_url
            
            # Complete job
            update_job_progress(job_id, 1.0, "Enhancement complete")
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            # Store results
            job.result_data.update({
                "findings": {
                    "static": len(static_findings),
                    "dynamic": len(dynamic_findings),
                    "mutation": mutation_results
                },
                "proposals": len(feature_proposals),
                "refactor_plans": len(refactor_plans)
            })
            
            logger.info(f"Enhancement job {job_id} completed successfully")
            
        finally:
            # Clean up clone
            from agent.ingestion.clone import cleanup_clone
            cleanup_clone(clone_path)
            
    except Exception as e:
        logger.error(f"Error in enhancement job {job_id}: {e}")
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)


def update_job_progress(job_id: str, progress: float, message: str):
    """
    Update the progress of a job.
    
    Args:
        job_id: Job ID
        progress: Progress value (0.0 to 1.0)
        message: Progress message
    """
    if job_id in jobs:
        job = jobs[job_id]
        job.progress = progress
        job.result_data["progress_message"] = message
        logger.debug(f"Job {job_id} progress: {progress:.2%} - {message}")


def generate_codebase_summary(
    parse_units: List,
    static_findings: List,
    dynamic_findings: List
) -> str:
    """
    Generate a summary of the codebase.
    
    Args:
        parse_units: List of parse units
        static_findings: List of static findings
        dynamic_findings: List of dynamic findings
        
    Returns:
        Codebase summary
    """
    # Count files by language
    languages = {}
    for unit in parse_units:
        lang = unit.language.value
        if lang not in languages:
            languages[lang] = 0
        languages[lang] += 1
    
    # Count symbols by type
    symbol_types = {}
    for unit in parse_units:
        for symbol in unit.symbols:
            sym_type = symbol.type.value
            if sym_type not in symbol_types:
                symbol_types[sym_type] = 0
            symbol_types[sym_type] += 1
    
    # Create summary
    summary = f"Codebase with {len(parse_units)} files in {len(languages)} languages: "
    summary += ", ".join([f"{count} {lang}" for lang, count in languages.items()])
    
    if symbol_types:
        summary += f". Symbols: {', '.join([f'{count} {stype}' for stype, count in symbol_types.items()])}"
    
    if static_findings or dynamic_findings:
        summary += f". Issues: {len(static_findings)} static, {len(dynamic_findings)} dynamic."
    
    return summary
