#!/bin/bash

# Database seeding script

set -e

echo "Seeding database with initial data..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USER=${NEO4J_USER:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"}
export POSTGRES_URI=${POSTGRES_URI:-"postgresql://postgres:password@localhost:5432/autonomous_code_improver"}

# Run Python seeding script
python -c "
import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from agent.core.models import Finding, FeatureProposal, RefactorPlan, Severity, FindingType
from agent.memory.store import MemoryStore
from agent.graph.service import GraphService

# Initialize services
print('Connecting to services...')
graph_service = GraphService(
    uri=os.getenv('NEO4J_URI'),
    user=os.getenv('NEO4J_USER'),
    password=os.getenv('NEO4J_PASSWORD')
)
graph_service.connect()

memory_store = MemoryStore(os.getenv('POSTGRES_URI'))
memory_store.connect()

# Create a sample repository
repo_id = uuid.uuid4()
print(f'Creating sample repository with ID: {repo_id}')

# Create sample findings
print('Creating sample findings...')
findings = [
    Finding(
        id=uuid.uuid4(),
        repo_id=repo_id,
        type=FindingType.SECURITY,
        severity=Severity.HIGH,
        title='SQL Injection Vulnerability',
        description='Potential SQL injection vulnerability in query construction',
        file_path='src/database.py',
        start_line=42,
        end_line=45,
        rule_id='B608',
        metadata={'tool': 'bandit', 'cwe': 'CWE-89'}
    ),
    Finding(
        id=uuid.uuid4(),
        repo_id=repo_id,
        type=FindingType.PERFORMANCE,
        severity=Severity.MEDIUM,
        title='Inefficient Loop',
        description='Loop has O(n^2) complexity, consider optimizing',
        file_path='src/processing.py',
        start_line=78,
        end_line=85,
        rule_id='PERF401',
        metadata={'tool': 'ruff', 'complexity': 'O(n^2)'}
    ),
    Finding(
        id=uuid.uuid4(),
        repo_id=repo_id,
        type=FindingType.STYLE,
        severity=Severity.LOW,
        title='Missing Docstring',
        description='Function is missing a docstring',
        file_path='src/utils.py',
        start_line=15,
        end_line=20,
        rule_id='D100',
        metadata={'tool': 'ruff', 'pep8': 'D100'}
    )
]

# Store findings
for finding in findings:
    memory_store.store_finding(finding)

# Create sample feature proposals
print('Creating sample feature proposals...')
proposals = [
    FeatureProposal(
        id=uuid.uuid4(),
        repo_id=repo_id,
        title='Add Caching Layer',
        description='Implement a caching layer to improve performance for frequently accessed data',
        rationale='Current implementation makes repeated database calls for the same data, leading to performance issues',
        acceptance_criteria=[
            'Cache should have configurable TTL',
            'Cache should support multiple backends (memory, Redis)',
            'Cache should have a hit rate metric',
            'Cache should be transparent to existing code'
        ],
        estimated_effort='medium',
        risk_level=Severity.MEDIUM,
        cost_benefit_analysis={
            'benefits': ['Reduced database load', 'Faster response times', 'Better scalability'],
            'risks': ['Cache invalidation issues', 'Increased memory usage', 'Stale data'],
            'estimated_effort': 'medium'
        },
        testability_notes='Feature is highly testable with mock caches and integration tests'
    ),
    FeatureProposal(
        id=uuid.uuid4(),
        repo_id=repo_id,
        title='Implement API Rate Limiting',
        description='Add rate limiting to API endpoints to prevent abuse',
        rationale='Current API has no rate limiting, making it vulnerable to DoS attacks and abuse',
        acceptance_criteria=[
            'Rate limits should be configurable per endpoint',
            'Rate limits should be based on API key or IP address',
            'Rate limit exceeded should return HTTP 429',
            'Rate limits should be documented in API spec'
        ],
        estimated_effort='low',
        risk_level=Severity.LOW,
        cost_benefit_analysis={
            'benefits': ['Prevents abuse', 'Improves reliability', 'Fair resource usage'],
            'risks': ['Legitimate users might be blocked', 'Implementation complexity'],
            'estimated_effort': 'low'
        },
        testability_notes='Feature can be tested with integration tests and load testing'
    )
]

# Store proposals
for proposal in proposals:
    memory_store.store_feature_proposal(proposal)

# Create sample refactor plans
print('Creating sample refactor plans...')
plans = [
    RefactorPlan(
        id=uuid.uuid4(),
        repo_id=repo_id,
        title='Refactor Database Access Layer',
        description='Extract database access logic into a separate layer to improve testability and maintainability',
        target_files=['src/database.py', 'src/models.py'],
        risk_level=Severity.MEDIUM,
        estimated_effort='high',
        changes=[
            {
                'title': 'Create Repository Pattern',
                'description': 'Implement repository pattern for data access',
                'code_changes': 'Create base repository class and specific repositories for each model',
                'benefits': ['Better separation of concerns', 'Easier testing', 'Consistent API'],
                'risks': ['Initial implementation effort', 'Learning curve for team'],
                'mitigations': ['Implement incrementally', 'Provide documentation and training']
            },
            {
                'title': 'Add Connection Pooling',
                'description': 'Implement database connection pooling',
                'code_changes': 'Configure connection pool in database module',
                'benefits': ['Improved performance', 'Better resource management'],
                'risks': ['Connection leaks', 'Configuration complexity'],
                'mitigations': ['Use well-tested library', 'Monitor connection usage']
            }
        ]
    ),
    RefactorPlan(
        id=uuid.uuid4(),
        repo_id=repo_id,
        title='Extract Configuration Management',
        description='Centralize configuration management to improve maintainability',
        target_files=['src/config.py', 'src/settings.py'],
        risk_level=Severity.LOW,
        estimated_effort='low',
        changes=[
            {
                'title': 'Use Configuration Library',
                'description': 'Replace ad-hoc configuration with a proper library',
                'code_changes': 'Integrate a configuration management library',
                'benefits': ['Type safety', 'Environment-specific configs', 'Validation'],
                'risks': ['Library dependency', 'Migration effort'],
                'mitigations': ['Choose stable library', 'Migrate incrementally']
            }
        ]
    )
]

# Store plans
for plan in plans:
    memory_store.store_refactor_plan(plan)

# Store sample outcomes
print('Storing sample outcomes...')
memory_store.store_outcome(
    repo_id=str(repo_id),
    job_type='enhancement',
    job_id=str(uuid.uuid4()),
    outcome='completed',
    metrics={
        'duration_seconds': 245,
        'findings_count': 12,
        'proposals_count': 3,
        'refactor_plans_count': 2
    },
    metadata={'dry_run': False}
)

# Store sample feedback
print('Storing sample feedback...')
memory_store.store_feedback(
    repo_id=str(repo_id),
    entity_type='finding',
    entity_id=str(findings[0].id),
    feedback_type='accuracy',
    feedback_value=0.9,
    feedback_text='Accurate identification of SQL injection vulnerability',
    metadata={'reviewer': 'security-expert'}
)

print('Database seeding complete!')
"

echo "Database seeding complete!"
