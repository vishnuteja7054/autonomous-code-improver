
### 24. scripts/doctor.py

```python
#!/usr/bin/env python3
"""
System health check script for the Autonomous Code Improver.
"""

import os
import sys
import time
import json
from typing import Dict, List, Tuple, Any
from urllib.parse import urlparse

import httpx
import psycopg2
import redis
import requests
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class SystemHealthChecker:
    """Check the health of the Autonomous Code Improver system."""

    def __init__(self):
        """Initialize the health checker."""
        self.issues = []
        self.recommendations = []
        self.results = {}

    def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        console.print(Panel("[bold blue]System Health Check[/bold blue]", expand=False))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Check environment variables
            progress.add_task("Checking environment variables...", total=None)
            self.check_environment_variables()
            
            # Check services
            progress.add_task("Checking services...", total=None)
            self.check_services()
            
            # Check application
            progress.add_task("Checking application...", total=None)
            self.check_application()
            
            # Check databases
            progress.add_task("Checking databases...", total=None)
            self.check_databases()
            
            # Check resources
            progress.add_task("Checking resources...", total=None)
            self.check_resources()
        
        # Generate report
        self.generate_report()
        
        return self.results

    def check_environment_variables(self) -> None:
        """Check required environment variables."""
        logger.info("Checking environment variables...")
        
        required_vars = [
            "NEO4J_URI",
            "NEO4J_USER",
            "NEO4J_PASSWORD",
            "POSTGRES_URI",
            "REDIS_URL",
            "NATS_URL",
            "LLM_ENDPOINT",
            "GITHUB_TOKEN"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
            self.recommendations.append("Set missing environment variables in your .env file")
            self.results["environment_variables"] = {"status": "error", "missing": missing_vars}
        else:
            self.results["environment_variables"] = {"status": "ok"}

    def check_services(self) -> None:
        """Check if required services are running."""
        logger.info("Checking services...")
        
        services = [
            ("Neo4j", os.getenv("NEO4J_URI", "bolt://localhost:7687")),
            ("PostgreSQL", os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/postgres")),
            ("Redis", os.getenv("REDIS_URL", "redis://localhost:6379")),
            ("NATS", os.getenv("NATS_URL", "nats://localhost:4222")),
            ("LLM Endpoint", os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1"))
        ]
        
        service_status = {}
        
        for name, url in services:
            try:
                if name == "Neo4j":
                    self.check_neo4j(url)
                    service_status[name] = "ok"
                elif name == "PostgreSQL":
                    self.check_postgresql(url)
                    service_status[name] = "ok"
                elif name == "Redis":
                    self.check_redis(url)
                    service_status[name] = "ok"
                elif name == "NATS":
                    self.check_nats(url)
                    service_status[name] = "ok"
                elif name == "LLM Endpoint":
                    self.check_llm_endpoint(url)
                    service_status[name] = "ok"
                
                logger.info(f"✓ {name} is available")
            except Exception as e:
                logger.error(f"✗ {name} is not available: {e}")
                self.issues.append(f"{name} service is not available: {e}")
                service_status[name] = "error"
        
        self.results["services"] = service_status

    def check_neo4j(self, uri: str) -> None:
        """Check if Neo4j is available."""
        from neo4j import GraphDatabase
        
        parsed = urlparse(uri)
        driver = GraphDatabase.driver(
            uri,
            auth=(parsed.username or "neo4j", parsed.password or "password")
        )
        
        with driver.session() as session:
            session.run("RETURN 1")
        
        driver.close()

    def check_postgresql(self, uri: str) -> None:
        """Check if PostgreSQL is available."""
        conn = psycopg2.connect(uri)
        conn.close()

    def check_redis(self, uri: str) -> None:
        """Check if Redis is available."""
        client = redis.from_url(uri)
        client.ping()
        client.close()

    def check_nats(self, uri: str) -> None:
        """Check if NATS is available."""
        import nats
        
        nc = nats.connect(uri)
        nc.close()

    def check_llm_endpoint(self, url: str) -> None:
        """Check if the LLM endpoint is available."""
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()

    def check_application(self) -> None:
        """Check if the application is running."""
        logger.info("Checking application...")
        
        api_url = "http://localhost:8000"
        
        try:
            response = httpx.get(f"{api_url}/", timeout=5.0)
            if response.status_code == 200:
                self.results["application"] = {"status": "ok"}
                logger.info("✓ Application is running")
            else:
                self.issues.append(f"Application returned status code {response.status_code}")
                self.results["application"] = {"status": "error", "status_code": response.status_code}
        except Exception as e:
            logger.error(f"✗ Application is not running: {e}")
            self.issues.append(f"Application is not running: {e}")
            self.results["application"] = {"status": "error", "error": str(e)}

    def check_databases(self) -> None:
        """Check database connectivity and schema."""
        logger.info("Checking databases...")
        
        # Check Neo4j schema
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            parsed = urlparse(uri)
            
            driver = GraphDatabase.driver(
                uri,
                auth=(parsed.username or "neo4j", parsed.password or "password")
            )
            
            with driver.session() as session:
                # Check if constraints exist
                result = session.run("SHOW CONSTRAINTS")
                constraints = list(result)
                
                if not constraints:
                    self.issues.append("Neo4j constraints are not set up")
                    self.recommendations.append("Run the initialization script to set up Neo4j constraints")
                    self.results["neo4j_schema"] = {"status": "error", "constraints": len(constraints)}
                else:
                    self.results["neo4j_schema"] = {"status": "ok", "constraints": len(constraints)}
            
            driver.close()
        except Exception as e:
            logger.error(f"✗ Error checking Neo4j schema: {e}")
            self.issues.append(f"Error checking Neo4j schema: {e}")
            self.results["neo4j_schema"] = {"status": "error", "error": str(e)}
        
        # Check PostgreSQL schema
        try:
            uri = os.getenv("POSTGRES_URI", "postgresql://postgres:password@localhost:5432/autonomous_code_improver")
            conn = psycopg2.connect(uri)
            
            with conn.cursor() as cursor:
                # Check if tables exist
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = ["findings", "feature_proposals", "refactor_plans", "outcomes", "feedback"]
                
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    self.issues.append(f"PostgreSQL tables are missing: {', '.join(missing_tables)}")
                    self.recommendations.append("Run the initialization script to set up PostgreSQL tables")
                    self.results["postgresql_schema"] = {"status": "error", "missing_tables": missing_tables}
                else:
                    self.results["postgresql_schema"] = {"status": "ok", "tables": len(tables)}
            
            conn.close()
        except Exception as e:
            logger.error(f"✗ Error checking PostgreSQL schema: {e}")
            self.issues.append(f"Error checking PostgreSQL schema: {e}")
            self.results["postgresql_schema"] = {"status": "error", "error": str(e)}

    def check_resources(self) -> None:
        """Check system resources."""
        logger.info("Checking resources...")
        
        # Check disk space
        try:
            import shutil
            
            total, used, free = shutil.disk_usage("/")
            free_percent = free / total * 100
            
            if free_percent < 10:
                self.issues.append(f"Low disk space: {free_percent:.1f}% free")
                self.recommendations.append("Clean up disk space or increase storage")
                self.results["disk_space"] = {"status": "error", "free_percent": free_percent}
            else:
                self.results["disk_space"] = {"status": "ok", "free_percent": free_percent}
        except Exception as e:
            logger.error(f"✗ Error checking disk space: {e}")
            self.results["disk_space"] = {"status": "error", "error": str(e)}
        
        # Check memory
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100
            
            if available_percent < 10:
                self.issues.append(f"Low memory: {available_percent:.1f}% available")
                self.recommendations.append("Free up memory or increase RAM")
                self.results["memory"] = {"status": "error", "available_percent": available_percent}
            else:
                self.results["memory"] = {"status": "ok", "available_percent": available_percent}
        except ImportError:
            logger.warning("psutil not available, skipping memory check")
            self.results["memory"] = {"status": "unknown", "reason": "psutil not available"}
        except Exception as e:
            logger.error(f"✗ Error checking memory: {e}")
            self.results["memory"] = {"status": "error", "error": str(e)}

    def generate_report(self) -> None:
        """Generate a health report."""
        console.print("\n")
        
        # Summary
        status = "ok" if not self.issues else "error"
        status_color = "green" if status == "ok" else "red"
        
        console.print(Panel(
            f"[bold]System Status: [{status_color}]{status.upper()}[/{status_color}][/bold]",
            title="Health Check Summary"
        ))
        
        # Issues
        if self.issues:
            console.print("\n[bold red]Issues Found:[/bold red]")
            for issue in self.issues:
                console.print(f"• {issue}")
        
        # Recommendations
        if self.recommendations:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in self.recommendations:
                console.print(f"• {rec}")
        
        # Detailed results
        console.print("\n[bold]Detailed Results:[/bold]")
        
        # Environment variables
        env_status = self.results.get("environment_variables", {})
        env_color = "green" if env_status.get("status") == "ok" else "red"
        console.print(f"Environment Variables: [{env_color}]{env_status.get('status', 'unknown')}[/{env_color}]")
        
        if env_status.get("missing"):
            console.print(f"  Missing: {', '.join(env_status['missing'])}")
        
        # Services
        services_status = self.results.get("services", {})
        console.print("\nServices:")
        
        for service, status in services_status.items():
            status_color = "green" if status == "ok" else "red"
            console.print(f"  {service}: [{status_color}]{status}[/{status_color}]")
        
        # Application
        app_status = self.results.get("application", {})
        app_color = "green" if app_status.get("status") == "ok" else "red"
        console.print(f"\nApplication: [{app_color}]{app_status.get('status', 'unknown')}[/{app_color}]")
        
        # Databases
        neo4j_status = self.results.get("neo4j_schema", {})
        neo4j_color = "green" if neo4j_status.get("status") == "ok" else "red"
        console.print(f"\nNeo4j Schema: [{neo4j_color}]{neo4j_status.get('status', 'unknown')}[/{neo4j_color}]")
        
        if neo4j_status.get("constraints") is not None:
            console.print(f"  Constraints: {neo4j_status['constraints']}")
        
        postgres_status = self.results.get("postgresql_schema", {})
        postgres_color = "green" if postgres_status.get("status") == "ok" else "red"
        console.print(f"PostgreSQL Schema: [{postgres_color}]{postgres_status.get('status', 'unknown')}[/{postgres_color}]")
        
        if postgres_status.get("tables") is not None:
            console.print(f"  Tables: {postgres_status['tables']}")
        
        # Resources
        disk_status = self.results.get("disk_space", {})
        disk_color = "green" if disk_status.get("status") == "ok" else "red"
        console.print(f"\nDisk Space: [{disk_color}]{disk_status.get('status', 'unknown')}[/{disk_color}]")
        
        if disk_status.get("free_percent") is not None:
            console.print(f"  Free: {disk_status['free_percent']:.1f}%")
        
        memory_status = self.results.get("memory", {})
        memory_color = "green" if memory_status.get("status") == "ok" else "red"
        console.print(f"Memory: [{memory_color}]{memory_status.get('status', 'unknown')}[/{memory_color}]")
        
        if memory_status.get("available_percent") is not None:
            console.print(f"  Available: {memory_status['available_percent']:.1f}%")
        
        # Save results to file
        with open("health-check.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        console.print(f"\nDetailed results saved to: health-check.json")


def main():
    """Main function."""
    try:
        checker = SystemHealthChecker()
        results = checker.check_all()
        
        # Exit with appropriate code
        if checker.issues:
            sys.exit(1)
        else:
            sys.exit(0)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Health check cancelled[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Error running health check: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
