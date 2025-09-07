"""
Repository cloning functionality.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import git
from git import Repo
from loguru import logger

from agent.core.models import RepoSpec


def clone_repository(repo_spec: RepoSpec, target_dir: Optional[str] = None) -> Tuple[str, Repo]:
    """
    Clone a Git repository to a local directory.
    
    Args:
        repo_spec: Repository specification
        target_dir: Optional target directory. If None, uses a temporary directory.
        
    Returns:
        Tuple of (clone_path, repo_object)
        
    Raises:
        git.GitCommandError: If cloning fails
        ValueError: If the repository URL is invalid
    """
    try:
        # Parse the repository URL to extract the repo name
        parsed_url = urlparse(repo_spec.url)
        repo_name = os.path.basename(parsed_url.path)
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        # Create target directory if not provided
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix=f"autonomous_code_improver_{repo_name}_")
        else:
            target_dir = os.path.abspath(target_dir)
            os.makedirs(target_dir, exist_ok=True)
            
        clone_path = os.path.join(target_dir, repo_name)
        
        # Clone the repository
        logger.info(f"Cloning repository {repo_spec.url} to {clone_path}")
        
        # Prepare clone arguments
        clone_args = {
            "url": repo_spec.url,
            "to_path": clone_path,
        }
        
        # Add branch or commit if specified
        if repo_spec.branch:
            clone_args["branch"] = repo_spec.branch
            logger.info(f"Cloning branch {repo_spec.branch}")
        elif repo_spec.commit:
            # For a specific commit, we first clone the default branch
            logger.info(f"Cloning repository and checking out commit {repo_spec.commit}")
            repo = Repo.clone_from(**clone_args)
            repo.git.checkout(repo_spec.commit)
            return clone_path, repo
            
        # Clone the repository
        repo = Repo.clone_from(**clone_args)
        
        logger.info(f"Successfully cloned repository to {clone_path}")
        return clone_path, repo
        
    except git.GitCommandError as e:
        logger.error(f"Failed to clone repository: {e}")
        # Clean up on failure
        if target_dir is None and os.path.exists(clone_path):
            shutil.rmtree(clone_path)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during repository cloning: {e}")
        # Clean up on failure
        if target_dir is None and clone_path and os.path.exists(clone_path):
            shutil.rmtree(clone_path)
        raise ValueError(f"Invalid repository URL or cloning failed: {e}")


def cleanup_clone(clone_path: str) -> None:
    """
    Clean up a cloned repository directory.
    
    Args:
        clone_path: Path to the cloned repository
    """
    try:
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)
            logger.info(f"Cleaned up clone directory: {clone_path}")
    except Exception as e:
        logger.error(f"Failed to clean up clone directory {clone_path}: {e}")


def get_repo_info(repo_path: str) -> dict:
    """
    Get information about a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with repository information
    """
    try:
        repo = Repo(repo_path)
        
        # Get the current commit
        commit = repo.head.commit
        
        # Get the current branch
        branch = repo.active_branch.name
        
        # Get the remote URL
        remote_url = None
        if repo.remotes:
            remote_url = repo.remotes[0].url
            
        # Get the repository size (approximate)
        size = 0
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not os.path.islink(file_path):
                    size += os.path.getsize(file_path)
                    
        return {
            "path": repo_path,
            "branch": branch,
            "commit": commit.hexsha,
            "commit_message": commit.message,
            "commit_date": commit.committed_datetime.isoformat(),
            "author": commit.author.name,
            "remote_url": remote_url,
            "size_bytes": size,
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files,
        }
    except Exception as e:
        logger.error(f"Failed to get repository info for {repo_path}: {e}")
        return {
            "path": repo_path,
            "error": str(e),
        }
