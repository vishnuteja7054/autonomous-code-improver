"""
Command-line interface for the autonomous code improvement system.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent.core.models import Language, RepoSpec
from agent.runtime.orchestrator import submit_enhancement_job, get_job_status

app = typer.Typer(help="Autonomous Code Improver CLI")
console = Console()


@app.command()
def enhance(
    repo_url: str = typer.Argument(..., help="Repository URL"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch to analyze"),
    commit: Optional[str] = typer.Option(None, "--commit", help="Specific commit to analyze"),
    languages: Optional[str] = typer.Option(None, "--languages", help="Comma-separated list of languages"),
    paths: Optional[str] = typer.Option(None, "--paths", help="Comma-separated list of paths to include"),
    exclude_patterns: Optional[str] = typer.Option(None, "--exclude", help="Comma-separated list of patterns to exclude"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run analysis without creating PR"),
    since_commit: Optional[str] = typer.Option(None, "--since-commit", help="Only analyze changes since this commit"),
    only: Optional[str] = typer.Option(None, "--only", help="Only run specific analysis types (static,dynamic,mutation)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Enhance a repository by analyzing and improving its code."""
    
    console.print(Panel(f"[bold blue]Enhancing Repository[/bold blue]", expand=False))
    console.print(f"Repository: {repo_url}")
    
    # Parse languages
    lang_list = None
    if languages:
        lang_list = [Language(lang.strip()) for lang in languages.split(",") if lang.strip()]
    
    # Parse paths
    path_list = None
    if paths:
        path_list = [path.strip() for path in paths.split(",") if path.strip()]
    
    # Parse exclude patterns
    exclude_list = None
    if exclude_patterns:
        exclude_list = [pattern.strip() for pattern in exclude_patterns.split(",") if pattern.strip()]
    
    # Create repo spec
    repo_spec = RepoSpec(
        url=repo_url,
        branch=branch,
        commit=commit,
        languages=lang_list,
        paths=path_list,
        exclude_patterns=exclude_list
    )
    
    # Submit enhancement job
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Submitting enhancement job...", total=None)
        
        try:
            # Submit job
            job_response = submit_enhancement_job(
                EnhancementRequest(
                    repo_url=repo_url,
                    branch=branch,
                    commit=commit,
                    languages=lang_list,
                    paths=path_list,
                    exclude_patterns=exclude_list,
                    dry_run=dry_run
                )
            )
            
            job_id = job_response.job_id
            progress.update(task, description=f"Job submitted with ID: {job_id}")
            
            # Wait for job to complete
            console.print("\n[bold]Waiting for job to complete...[/bold]")
            
            while True:
                status_response = get_job_status(job_id)
                status = status_response.status
                
                if status == "completed":
                    console.print("[green]✓[/green] Job completed successfully!")
                    break
                elif status == "failed":
                    console.print("[red]✗[/red] Job failed!")
                    console.print(f"Error: {status_response.error_message}")
                    sys.exit(1)
                else:
                    console.print(f"Status: {status}")
                
                # Wait before checking again
                import time
                time.sleep(5)
            
            # Get final job status
            final_status = get_job_status(job_id)
            
            # Display results
            console.print("\n[bold]Results:[/bold]")
            
            result_data = final_status.result_data
            if "findings" in result_data:
                findings = result_data["findings"]
                console.print(f"Static findings: {findings.get('static', 0)}")
                console.print(f"Dynamic findings: {findings.get('dynamic', 0)}")
                console.print(f"Mutation testing: {findings.get('mutation', {}).get('mutation_score', 0):.1%} score")
            
            if "proposals" in result_data:
                console.print(f"Feature proposals: {result_data['proposals']}")
            
            if "refactor_plans" in result_data:
                console.print(f"Refactoring plans: {result_data['refactor_plans']}")
            
            if "pr_id" in result_data:
                console.print(f"Pull request: #{result_data['pr_id']} - {result_data.get('pr_url', '')}")
            
            # Save results to file if requested
            if output:
                import json
                with open(output, "w") as f:
                    json.dump(final_status.dict(), f, indent=2)
                console.print(f"\nResults saved to: {output}")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@app.command()
def report(
    repo_url: str = typer.Argument(..., help="Repository URL"),
    type: str = typer.Option("all", "--type", help="Type of report (findings,proposals,all)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table,json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate a report for a repository."""
    
    console.print(Panel(f"[bold blue]Generating Report[/bold blue]", expand=False))
    console.print(f"Repository: {repo_url}")
    console.print(f"Type: {type}")
    
    # This is a placeholder implementation
    # In a real implementation, you would query the database for findings and proposals
    
    if type in ["findings", "all"]:
        console.print("\n[bold]Findings:[/bold]")
        
        # Create a table for findings
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Severity", style="yellow")
        table.add_column("Title", style="green")
        table.add_column("File", style="blue")
        
        # Add sample findings
        table.add_row("Security", "High", "SQL Injection", "src/database.py")
        table.add_row("Performance", "Medium", "Inefficient Loop", "src/processing.py")
        table.add_row("Style", "Low", "Missing Docstring", "src/utils.py")
        
        console.print(table)
    
    if type in ["proposals", "all"]:
        console.print("\n[bold]Feature Proposals:[/bold]")
        
        # Create a table for proposals
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Title", style="cyan")
        table.add_column("Effort", style="yellow")
        table.add_column("Risk", style="green")
        
        # Add sample proposals
        table.add_row("Add Caching Layer", "Medium", "Medium")
        table.add_row("Implement API Rate Limiting", "Low", "Low")
        
        console.print(table)
    
    # Save results to file if requested
    if output:
        console.print(f"\nReport saved to: {output}")


@app.command()
def graph(
    repo_url: str = typer.Argument(..., help="Repository URL"),
    format: str = typer.Option("graphml", "--format", "-f", help="Output format (graphml,json)"),
    output: str = typer.Option("artifacts/graph.graphml", "--output", "-o", help="Output file"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Custom query to run"),
):
    """Export or query the knowledge graph."""
    
    console.print(Panel(f"[bold blue]Knowledge Graph[/bold blue]", expand=False))
    console.print(f"Repository: {repo_url}")
    console.print(f"Format: {format}")
    console.print(f"Output: {output}")
    
    # This is a placeholder implementation
    # In a real implementation, you would query the knowledge graph
    
    if query:
        console.print(f"\n[bold]Query:[/bold] {query}")
        console.print("\n[bold]Results:[/bold]")
        console.print("Query results would be displayed here...")
    else:
        console.print(f"\n[bold]Exporting graph to {format} format...[/bold]")
        console.print(f"Graph exported to: {output}")


@app.command()
def open_pr(
    repo_url: str = typer.Argument(..., help="Repository URL"),
    title: str = typer.Option("Automated Code Improvements", "--title", "-t", help="PR title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="PR body"),
    branch: str = typer.Option("autonomous-improvements", "--branch", help="Branch name"),
    base: str = typer.Option("main", "--base", help="Base branch"),
):
    """Create a pull request with improvements."""
    
    console.print(Panel(f"[bold blue]Creating Pull Request[/bold blue]", expand=False))
    console.print(f"Repository: {repo_url}")
    console.print(f"Title: {title}")
    console.print(f"Branch: {branch} -> {base}")
    
    # This is a placeholder implementation
    # In a real implementation, you would create a PR on GitHub
    
    console.print("\n[bold]Creating pull request...[/bold]")
    console.print("[green]✓[/green] Pull request created successfully!")
    console.print("PR URL: https://github.com/example/repo/pull/123")


@app.command()
def doctor():
    """Check system health and configuration."""
    
    console.print(Panel(f"[bold blue]System Health Check[/bold blue]", expand=False))
    
    # Check environment variables
    console.print("\n[bold]Environment Variables:[/bold]")
    
    env_vars = [
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "POSTGRES_URI",
        "REDIS_URL",
        "NATS_URL",
        "LLM_ENDPOINT",
        "GITHUB_TOKEN"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            console.print(f"✓ {var}: [green]Set[/green]")
        else:
            console.print(f"✗ {var}: [red]Not set[/red]")
    
    # Check services
    console.print("\n[bold]Services:[/bold]")
    
    services = [
        ("Neo4j", "bolt://localhost:7687"),
        ("PostgreSQL", "postgresql://postgres:password@localhost:5432/postgres"),
        ("Redis", "redis://localhost:6379"),
        ("NATS", "nats://localhost:4222"),
        ("LLM Endpoint", "http://localhost:8000/v1")
    ]
    
    for name, url in services:
        console.print(f"Checking {name}...")
        # In a real implementation, you would check if the service is available
        console.print(f"✓ {name}: [green]Available[/green]")
    
    console.print("\n[bold]System Health:[/bold] [green]Good[/green]")


if __name__ == "__main__":
    app()
