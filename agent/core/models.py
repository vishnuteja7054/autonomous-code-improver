"""
Core data models for the autonomous code improvement system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class Language(str, Enum):
    """Programming languages supported by the system."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"


class Severity(str, Enum):
    """Severity levels for findings and issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(str, Enum):
    """Types of findings that can be discovered."""
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    STYLE = "style"
    ARCHITECTURE = "architecture"


class SymbolType(str, Enum):
    """Types of symbols in the codebase."""
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    VARIABLE = "variable"
    CONSTANT = "constant"
    MODULE = "module"
    PACKAGE = "package"
    PARAMETER = "parameter"
    TYPE = "type"
    ENUM = "enum"
    STRUCT = "struct"
    TRAIT = "trait"


class EdgeType(str, Enum):
    """Types of edges in the knowledge graph."""
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    DEFINES = "defines"
    USES = "uses"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    INSTANTIATES = "instantiates"
    THROWS = "throws"
    CATCHES = "catches"
    OVERRIDES = "overrides"
    EXTENDS = "extends"


class RepoSpec(BaseModel):
    """Specification for a repository to analyze."""
    url: str = Field(..., description="Repository URL")
    branch: Optional[str] = Field(None, description="Branch to analyze")
    commit: Optional[str] = Field(None, description="Specific commit to analyze")
    languages: List[Language] = Field(default_factory=list, description="Languages to focus on")
    paths: List[str] = Field(default_factory=list, description="Paths to include/exclude")
    exclude_patterns: List[str] = Field(default_factory=list, description="Patterns to exclude")

    @validator("url")
    def validate_url(cls, v):
        if not v.startswith(("https://", "git@")):
            raise ValueError("Repository URL must start with https:// or git@")
        return v


class ParseUnit(BaseModel):
    """Unit of code to be parsed."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    path: str
    language: Language
    content: str
    ast: Optional[Dict[str, Any]] = None
    symbols: List["Symbol"] = Field(default_factory=list)
    edges: List["Edge"] = Field(default_factory=list)
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    size_bytes: int = Field(0, description="Size of the file in bytes")

    @validator("size_bytes", pre=True)
    def calculate_size(cls, v, values):
        if v == 0 and "content" in values:
            return len(values["content"].encode("utf-8"))
        return v


class Symbol(BaseModel):
    """Symbol in the codebase (function, class, variable, etc.)."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: SymbolType
    file_path: str
    language: Language
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    repo_id: UUID


class Edge(BaseModel):
    """Edge connecting two symbols in the knowledge graph."""
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    type: EdgeType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    repo_id: UUID


class Finding(BaseModel):
    """Finding from code analysis (bug, security issue, etc.)."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    type: FindingType
    severity: Severity
    title: str
    description: str
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    symbol_id: Optional[UUID] = None
    rule_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    false_positive: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None


class RefactorPlan(BaseModel):
    """Plan for refactoring code."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    title: str
    description: str
    target_symbols: List[UUID] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    risk_level: Severity
    estimated_effort: str  # e.g., "low", "medium", "high"
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)  # IDs of other refactor plans
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_by: Optional[str] = None
    implemented: bool = False
    implementation_notes: Optional[str] = None


class FeatureProposal(BaseModel):
    """Proposal for a new feature."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    title: str
    description: str
    rationale: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    estimated_effort: str  # e.g., "low", "medium", "high"
    risk_level: Severity
    cost_benefit_analysis: Dict[str, Any] = Field(default_factory=dict)
    testability_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_by: Optional[str] = None
    implemented: bool = False
    implementation_notes: Optional[str] = None


class Patch(BaseModel):
    """Patch to be applied to code."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    plan_id: Optional[UUID] = None  # RefactorPlan or FeatureProposal ID
    file_path: str
    original_content: str
    modified_content: str
    diff: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied: bool = False
    applied_at: Optional[datetime] = None
    rollback_available: bool = False
    rollback_content: Optional[str] = None


class TestPlan(BaseModel):
    """Plan for testing changes."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    patch_id: UUID
    test_type: str  # e.g., "unit", "integration", "e2e"
    test_files: List[str] = Field(default_factory=list)
    test_commands: List[str] = Field(default_factory=list)
    expected_outcome: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed: bool = False
    executed_at: Optional[datetime] = None
    passed: bool = False
    execution_output: Optional[str] = None
    coverage_percentage: Optional[float] = None


class BenchmarkPlan(BaseModel):
    """Plan for benchmarking changes."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    patch_id: UUID
    benchmark_type: str  # e.g., "performance", "memory", "throughput"
    benchmark_files: List[str] = Field(default_factory=list)
    benchmark_commands: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)  # e.g., "execution_time", "memory_usage"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed: bool = False
    executed_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    baseline_results: Optional[Dict[str, Any]] = None
    improvement_percentage: Optional[float] = None


class RiskReport(BaseModel):
    """Report on risks associated with changes."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    patch_id: UUID
    overall_risk_level: Severity
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    mitigations: List[Dict[str, Any]] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    benchmark_results: Optional[Dict[str, Any]] = None
    static_analysis_results: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_by: Optional[str] = None


class PRSummary(BaseModel):
    """Summary of a pull request."""
    id: UUID = Field(default_factory=uuid4)
    repo_id: UUID
    pr_id: Optional[int] = None  # GitHub PR ID
    pr_url: Optional[str] = None
    title: str
    description: str
    patches: List[UUID] = Field(default_factory=list)  # Patch IDs
    risk_report_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    merged: bool = False
    merged_at: Optional[datetime] = None
    closed: bool = False
    closed_at: Optional[datetime] = None
    review_comments: List[Dict[str, Any]] = Field(default_factory=list)
    ci_status: Optional[str] = None


class JobStatus(str, Enum):
    """Status of a background job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """Background job for processing tasks."""
    id: UUID = Field(default_factory=uuid4)
    job_type: str  # e.g., "ingestion", "analysis", "enhancement"
    repo_id: UUID
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMRequest(BaseModel):
    """Request to the LLM service."""
    id: UUID = Field(default_factory=uuid4)
    prompt: str
    model: str = "chatglm3-6b"
    temperature: float = 0.7
    max_tokens: int = 2048
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None


class SystemConfig(BaseModel):
    """System configuration."""
    llm_endpoint: str = "http://localhost:8000/v1"
    llm_model: str = "chatglm3-6b"
    llm_api_key: Optional[str] = None
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    postgres_uri: str = "postgresql://postgres:password@localhost:5432/autonomous_code_improver"
    redis_url: str = "redis://localhost:6379"
    nats_url: str = "nats://localhost:4222"
    github_token: Optional[str] = None
    vcs_host: str = "github"
    sandbox_image: str = "autonomous-code-improver-sandbox:latest"
    max_file_size_mb: int = 10
    timeout_seconds: int = 300
    log_level: str = "INFO"
    enable_telemetry: bool = True
