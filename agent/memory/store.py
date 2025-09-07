"""
Store for managing historical data and learning from outcomes.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from loguru import logger

from agent.core.models import Finding, FeatureProposal, RefactorPlan


class MemoryStore:
    """
    Store for managing historical data and learning from outcomes.
    """
    
    def __init__(self, db_uri: str):
        """
        Initialize the memory store.
        
        Args:
            db_uri: Database connection URI
        """
        self.db_uri = db_uri
        self.conn = None
        
    def connect(self) -> None:
        """Connect to the database."""
        try:
            self.conn = psycopg2.connect(self.db_uri)
            logger.info("Connected to memory store database")
            
            # Create tables if they don't exist
            self._create_tables()
            
        except Exception as e:
            logger.error(f"Failed to connect to memory store: {e}")
            raise
            
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed connection to memory store database")
            
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self.conn.cursor() as cur:
            # Create findings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id UUID PRIMARY KEY,
                    repo_id UUID NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT,
                    metadata JSONB
                )
            """)
            
            # Create feature_proposals table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feature_proposals (
                    id UUID PRIMARY KEY,
                    repo_id UUID NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    estimated_effort VARCHAR(20) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    approved BOOLEAN DEFAULT FALSE,
                    implemented BOOLEAN DEFAULT FALSE,
                    implementation_notes TEXT,
                    metadata JSONB
                )
            """)
            
            # Create refactor_plans table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS refactor_plans (
                    id UUID PRIMARY KEY,
                    repo_id UUID NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    estimated_effort VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    approved BOOLEAN DEFAULT FALSE,
                    implemented BOOLEAN DEFAULT FALSE,
                    implementation_notes TEXT,
                    metadata JSONB
                )
            """)
            
            # Create outcomes table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id UUID PRIMARY KEY,
                    repo_id UUID NOT NULL,
                    job_type VARCHAR(50) NOT NULL,
                    job_id UUID NOT NULL,
                    outcome VARCHAR(20) NOT NULL,
                    metrics JSONB,
                    created_at TIMESTAMP NOT NULL,
                    metadata JSONB
                )
            """)
            
            # Create feedback table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id UUID PRIMARY KEY,
                    repo_id UUID NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id UUID NOT NULL,
                    feedback_type VARCHAR(50) NOT NULL,
                    feedback_value FLOAT NOT NULL,
                    feedback_text TEXT,
                    created_at TIMESTAMP NOT NULL,
                    metadata JSONB
                )
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_repo_id ON findings(repo_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feature_proposals_repo_id ON feature_proposals(repo_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_refactor_plans_repo_id ON refactor_plans(repo_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_repo_id ON outcomes(repo_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_entity_id ON feedback(entity_id)")
            
            self.conn.commit()
            logger.info("Created database tables")
            
    def store_finding(self, finding: Finding) -> None:
        """
        Store a finding in the memory store.
        
        Args:
            finding: Finding to store
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO findings (
                    id, repo_id, type, severity, title, description, file_path,
                    created_at, resolved, resolution_notes, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    type = EXCLUDED.type,
                    severity = EXCLUDED.severity,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    file_path = EXCLUDED.file_path,
                    resolved = EXCLUDED.resolved,
                    resolution_notes = EXCLUDED.resolution_notes,
                    metadata = EXCLUDED.metadata
            """, (
                str(finding.id),
                str(finding.repo_id),
                finding.type.value,
                finding.severity.value,
                finding.title,
                finding.description,
                finding.file_path,
                finding.created_at,
                finding.resolved,
                finding.resolution_notes,
                json.dumps(finding.metadata)
            ))
            
            self.conn.commit()
            
    def store_feature_proposal(self, proposal: FeatureProposal) -> None:
        """
        Store a feature proposal in the memory store.
        
        Args:
            proposal: Feature proposal to store
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feature_proposals (
                    id, repo_id, title, description, estimated_effort, risk_level,
                    created_at, approved, implemented, implementation_notes, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    estimated_effort = EXCLUDED.estimated_effort,
                    risk_level = EXCLUDED.risk_level,
                    approved = EXCLUDED.approved,
                    implemented = EXCLUDED.implemented,
                    implementation_notes = EXCLUDED.implementation_notes,
                    metadata = EXCLUDED.metadata
            """, (
                str(proposal.id),
                str(proposal.repo_id),
                proposal.title,
                proposal.description,
                proposal.estimated_effort,
                proposal.risk_level.value,
                proposal.created_at,
                proposal.approved,
                proposal.implemented,
                proposal.implementation_notes,
                json.dumps({
                    "cost_benefit_analysis": proposal.cost_benefit_analysis,
                    "testability_notes": proposal.testability_notes
                })
            ))
            
            self.conn.commit()
            
    def store_refactor_plan(self, plan: RefactorPlan) -> None:
        """
        Store a refactor plan in the memory store.
        
        Args:
            plan: Refactor plan to store
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO refactor_plans (
                    id, repo_id, title, description, risk_level, estimated_effort,
                    created_at, approved, implemented, implementation_notes, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    risk_level = EXCLUDED.risk_level,
                    estimated_effort = EXCLUDED.estimated_effort,
                    approved = EXCLUDED.approved,
                    implemented = EXCLUDED.implemented,
                    implementation_notes = EXCLUDED.implementation_notes,
                    metadata = EXCLUDED.metadata
            """, (
                str(plan.id),
                str(plan.repo_id),
                plan.title,
                plan.description,
                plan.risk_level.value,
                plan.estimated_effort,
                plan.created_at,
                plan.approved,
                plan.implemented,
                plan.implementation_notes,
                json.dumps({
                    "changes": plan.changes,
                    "dependencies": plan.dependencies
                })
            ))
            
            self.conn.commit()
            
    def store_outcome(
        self,
        repo_id: str,
        job_type: str,
        job_id: str,
        outcome: str,
        metrics: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a job outcome in the memory store.
        
        Args:
            repo_id: Repository ID
            job_type: Type of job
            job_id: Job ID
            outcome: Outcome of the job
            metrics: Metrics associated with the outcome
            metadata: Additional metadata
        """
        import uuid
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO outcomes (
                    id, repo_id, job_type, job_id, outcome, metrics, created_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                repo_id,
                job_type,
                job_id,
                outcome,
                json.dumps(metrics),
                datetime.utcnow(),
                json.dumps(metadata or {})
            ))
            
            self.conn.commit()
            
    def store_feedback(
        self,
        repo_id: str,
        entity_type: str,
        entity_id: str,
        feedback_type: str,
        feedback_value: float,
        feedback_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store feedback in the memory store.
        
        Args:
            repo_id: Repository ID
            entity_type: Type of entity (e.g., "finding", "proposal")
            entity_id: ID of the entity
            feedback_type: Type of feedback (e.g., "accuracy", "usefulness")
            feedback_value: Numerical feedback value
            feedback_text: Textual feedback
            metadata: Additional metadata
        """
        import uuid
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feedback (
                    id, repo_id, entity_type, entity_id, feedback_type, feedback_value,
                    feedback_text, created_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                repo_id,
                entity_type,
                entity_id,
                feedback_type,
                feedback_value,
                feedback_text,
                datetime.utcnow(),
                json.dumps(metadata or {})
            ))
            
            self.conn.commit()
            
    def get_findings_by_repo(self, repo_id: str, limit: int = 100) -> List[Finding]:
        """
        Get findings for a repository.
        
        Args:
            repo_id: Repository ID
            limit: Maximum number of findings to return
            
        Returns:
            List of findings
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, repo_id, type, severity, title, description, file_path,
                       created_at, resolved, resolution_notes, metadata
                FROM findings
                WHERE repo_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (repo_id, limit))
            
            findings = []
            for row in cur.fetchall():
                finding = Finding(
                    id=uuid.UUID(row[0]),
                    repo_id=uuid.UUID(row[1]),
                    type=row[2],
                    severity=row[3],
                    title=row[4],
                    description=row[5],
                    file_path=row[6],
                    created_at=row[7],
                    resolved=row[8],
                    resolution_notes=row[9],
                    metadata=json.loads(row[10]) if row[10] else {}
                )
                findings.append(finding)
                
            return findings
            
    def get_feature_proposals_by_repo(self, repo_id: str, limit: int = 100) -> List[FeatureProposal]:
        """
        Get feature proposals for a repository.
        
        Args:
            repo_id: Repository ID
            limit: Maximum number of proposals to return
            
        Returns:
            List of feature proposals
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, repo_id, title, description, estimated_effort, risk_level,
                       created_at, approved, implemented, implementation_notes, metadata
                FROM feature_proposals
                WHERE repo_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (repo_id, limit))
            
            proposals = []
            for row in cur.fetchall():
                metadata = json.loads(row[10]) if row[10] else {}
                
                proposal = FeatureProposal(
                    id=uuid.UUID(row[0]),
                    repo_id=uuid.UUID(row[1]),
                    title=row[2],
                    description=row[3],
                    estimated_effort=row[4],
                    risk_level=row[5],
                    created_at=row[6],
                    approved=row[7],
                    implemented=row[8],
                    implementation_notes=row[9],
                    cost_benefit_analysis=metadata.get("cost_benefit_analysis", {}),
                    testability_notes=metadata.get("testability_notes")
                )
                proposals.append(proposal)
                
            return proposals
            
    def get_refactor_plans_by_repo(self, repo_id: str, limit: int = 100) -> List[RefactorPlan]:
        """
        Get refactor plans for a repository.
        
        Args:
            repo_id: Repository ID
            limit: Maximum number of plans to return
            
        Returns:
            List of refactor plans
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, repo_id, title, description, risk_level, estimated_effort,
                       created_at, approved, implemented, implementation_notes, metadata
                FROM refactor_plans
                WHERE repo_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (repo_id, limit))
            
            plans = []
            for row in cur.fetchall():
                metadata = json.loads(row[10]) if row[10] else {}
                
                plan = RefactorPlan(
                    id=uuid.UUID(row[0]),
                    repo_id=uuid.UUID(row[1]),
                    title=row[2],
                    description=row[3],
                    risk_level=row[4],
                    estimated_effort=row[5],
                    created_at=row[6],
                    approved=row[7],
                    implemented=row[8],
                    implementation_notes=row[9],
                    changes=metadata.get("changes", []),
                    dependencies=metadata.get("dependencies", [])
                )
                plans.append(plan)
                
            return plans
            
    def get_outcomes_by_repo(
        self, 
        repo_id: str, 
        job_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get outcomes for a repository.
        
        Args:
            repo_id: Repository ID
            job_type: Filter by job type
            days: Number of days to look back
            
        Returns:
            List of outcomes
        """
        with self.conn.cursor() as cur:
            query = """
                SELECT id, repo_id, job_type, job_id, outcome, metrics, created_at, metadata
                FROM outcomes
                WHERE repo_id = %s AND created_at >= %s
            """
            
            params = [repo_id, datetime.utcnow() - timedelta(days=days)]
            
            if job_type:
                query += " AND job_type = %s"
                params.append(job_type)
                
            query += " ORDER BY created_at DESC"
            
            cur.execute(query, params)
            
            outcomes = []
            for row in cur.fetchall():
                outcome = {
                    "id": row[0],
                    "repo_id": row[1],
                    "job_type": row[2],
                    "job_id": row[3],
                    "outcome": row[4],
                    "metrics": json.loads(row[5]) if row[5] else {},
                    "created_at": row[6],
                    "metadata": json.loads(row[7]) if row[7] else {}
                }
                outcomes.append(outcome)
                
            return outcomes
            
    def get_feedback_by_entity(
        self, 
        entity_type: str, 
        entity_id: str,
        feedback_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get feedback for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            feedback_type: Filter by feedback type
            
        Returns:
            List of feedback entries
        """
        with self.conn.cursor() as cur:
            query = """
                SELECT id, repo_id, entity_type, entity_id, feedback_type, feedback_value,
                       feedback_text, created_at, metadata
                FROM feedback
                WHERE entity_type = %s AND entity_id = %s
            """
            
            params = [entity_type, entity_id]
            
            if feedback_type:
                query += " AND feedback_type = %s"
                params.append(feedback_type)
                
            query += " ORDER BY created_at DESC"
            
            cur.execute(query, params)
            
            feedback_list = []
            for row in cur.fetchall():
                feedback = {
                    "id": row[0],
                    "repo_id": row[1],
                    "entity_type": row[2],
                    "entity_id": row[3],
                    "feedback_type": row[4],
                    "feedback_value": row[5],
                    "feedback_text": row[6],
                    "created_at": row[7],
                    "metadata": json.loads(row[8]) if row[8] else {}
                }
                feedback_list.append(feedback)
                
            return feedback_list
            
    def get_success_rate_by_job_type(self, job_type: str, days: int = 30) -> float:
        """
        Get the success rate for a job type.
        
        Args:
            job_type: Type of job
            days: Number of days to look back
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN outcome = 'completed' THEN 1 ELSE 0 END) as successful
                FROM outcomes
                WHERE job_type = %s AND created_at >= %s
            """, (job_type, datetime.utcnow() - timedelta(days=days)))
            
            row = cur.fetchone()
            total = row[0]
            successful = row[1]
            
            if total == 0:
                return 0.0
                
            return successful / total
            
    def get_average_feedback_by_type(
        self, 
        entity_type: str, 
        feedback_type: str,
        days: int = 30
    ) -> float:
        """
        Get the average feedback value for an entity type and feedback type.
        
        Args:
            entity_type: Type of entity
            feedback_type: Type of feedback
            days: Number of days to look back
            
        Returns:
            Average feedback value
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(feedback_value)
                FROM feedback
                WHERE entity_type = %s AND feedback_type = %s AND created_at >= %s
            """, (entity_type, feedback_type, datetime.utcnow() - timedelta(days=days)))
            
            row = cur.fetchone()
            return row[0] or 0.0
