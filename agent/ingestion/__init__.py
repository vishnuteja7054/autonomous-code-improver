"""
Ingestion module for cloning, indexing, and parsing code repositories.
"""

from .clone import clone_repository
from .indexer import index_repository
from .parser import parse_file

__all__ = ["clone_repository", "index_repository", "parse_file"]
