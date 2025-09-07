"""
Repository indexing functionality.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

from agent.core.models import Language, ParseUnit, RepoSpec


def index_repository(repo_path: str, repo_spec: RepoSpec) -> List[ParseUnit]:
    """
    Index a repository and create parse units for each file.
    
    Args:
        repo_path: Path to the cloned repository
        repo_spec: Repository specification
        
    Returns:
        List of parse units for each file
    """
    logger.info(f"Indexing repository at {repo_path}")
    
    parse_units = []
    
    # Determine which files to process
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip files that match exclude patterns
            if should_exclude_file(rel_path, repo_spec.exclude_patterns):
                logger.debug(f"Skipping excluded file: {rel_path}")
                continue
                
            # Determine file language
            language = detect_language(file)
            if not language:
                logger.debug(f"Skipping unsupported file: {rel_path}")
                continue
                
            # Skip if language is not in the list of languages to process
            if repo_spec.languages and language not in repo_spec.languages:
                logger.debug(f"Skipping file with unsupported language: {rel_path}")
                continue
                
            # Skip binary files
            if is_binary_file(file_path):
                logger.debug(f"Skipping binary file: {rel_path}")
                continue
                
            # Skip files that are too large
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Skipping large file: {rel_path} ({file_size} bytes)")
                continue
                
            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.warning(f"Skipping file with encoding issues: {rel_path}")
                continue
                
            # Create parse unit
            parse_unit = ParseUnit(
                repo_id=repo_spec.id,  # This would be set in the caller
                path=rel_path,
                language=language,
                content=content,
                size_bytes=file_size,
            )
            
            parse_units.append(parse_unit)
    
    logger.info(f"Indexed {len(parse_units)} files")
    return parse_units


def should_exclude_file(file_path: str, exclude_patterns: List[str]) -> bool:
    """
    Check if a file should be excluded based on patterns.
    
    Args:
        file_path: Relative path to the file
        exclude_patterns: List of patterns to exclude
        
    Returns:
        True if the file should be excluded
    """
    if not exclude_patterns:
        return False
        
    for pattern in exclude_patterns:
        if pattern.startswith("*"):
            # Suffix pattern
            if file_path.endswith(pattern[1:]):
                return True
        elif pattern.endswith("*"):
            # Prefix pattern
            if file_path.startswith(pattern[:-1]):
                return True
        elif "*" in pattern:
            # Glob pattern
            import fnmatch
            if fnmatch.fnmatch(file_path, pattern):
                return True
        else:
            # Exact match
            if file_path == pattern:
                return True
                
    return False


def detect_language(file_path: str) -> Optional[Language]:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language or None if not supported
    """
    ext = Path(file_path).suffix.lower()
    
    language_map = {
        ".py": Language.PYTHON,
        ".js": Language.JAVASCRIPT,
        ".ts": Language.TYPESCRIPT,
        ".jsx": Language.JAVASCRIPT,
        ".tsx": Language.TYPESCRIPT,
        ".java": Language.JAVA,
        ".go": Language.GO,
        ".rs": Language.RUST,
        ".c": Language.C,
        ".cpp": Language.CPP,
        ".cc": Language.CPP,
        ".cxx": Language.CPP,
        ".c++": Language.CPP,
        ".h": Language.CPP,  # Could be C or C++, assume C++
        ".hpp": Language.CPP,
        ".cs": Language.CSHARP,
    }
    
    return language_map.get(ext)


def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is binary
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def get_file_stats(repo_path: str) -> Dict[str, any]:
    """
    Get statistics about the files in a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with file statistics
    """
    stats = {
        "total_files": 0,
        "files_by_language": {},
        "total_size_bytes": 0,
        "largest_file": None,
        "smallest_file": None,
    }
    
    largest_size = 0
    smallest_size = float("inf")
    largest_file = None
    smallest_file = None
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip directories and symlinks
            if os.path.isdir(file_path) or os.path.islink(file_path):
                continue
                
            # Skip binary files
            if is_binary_file(file_path):
                continue
                
            # Get file size
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                continue
                
            # Update total size
            stats["total_size_bytes"] += file_size
            
            # Update largest and smallest files
            if file_size > largest_size:
                largest_size = file_size
                largest_file = rel_path
                
            if file_size < smallest_size and file_size > 0:
                smallest_size = file_size
                smallest_file = rel_path
                
            # Detect language
            language = detect_language(file_path)
            if language:
                lang_key = language.value
                if lang_key not in stats["files_by_language"]:
                    stats["files_by_language"][lang_key] = {
                        "count": 0,
                        "total_size_bytes": 0,
                    }
                stats["files_by_language"][lang_key]["count"] += 1
                stats["files_by_language"][lang_key]["total_size_bytes"] += file_size
                
            stats["total_files"] += 1
    
    stats["largest_file"] = {
        "path": largest_file,
        "size_bytes": largest_size,
    }
    
    stats["smallest_file"] = {
        "path": smallest_file,
        "size_bytes": smallest_size,
    }
    
    return stats
