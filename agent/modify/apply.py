"""
Apply patches to code files.
"""

import difflib
import os
from typing import Optional

from loguru import logger

from agent.core.models import Patch


def apply_patch(patch: Patch, repo_path: str) -> bool:
    """
    Apply a patch to a file in the repository.
    
    Args:
        patch: Patch to apply
        repo_path: Path to the repository
        
    Returns:
        True if the patch was applied successfully, False otherwise
    """
    logger.info(f"Applying patch to {patch.file_path}")
    
    try:
        # Construct full file path
        file_path = os.path.join(repo_path, patch.file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Read current content
        with open(file_path, "r", encoding="utf-8") as f:
            current_content = f.read()
            
        # Verify that the current content matches the expected original content
        if current_content != patch.original_content:
            logger.error(f"File content has changed since patch was created")
            return False
            
        # Create backup
        backup_path = f"{file_path}.bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(current_content)
            
        # Apply the patch
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(patch.modified_content)
            
        # Verify the patch was applied correctly
        with open(file_path, "r", encoding="utf-8") as f:
            applied_content = f.read()
            
        if applied_content != patch.modified_content:
            logger.error("Patch was not applied correctly")
            # Restore from backup
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current_content)
            os.remove(backup_path)
            return False
            
        # Update patch status
        patch.applied = True
        patch.applied_at = datetime.utcnow()
        patch.rollback_content = current_content
        patch.rollback_available = True
        
        logger.info(f"Successfully applied patch to {patch.file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying patch: {e}")
        return False


def rollback_patch(patch: Patch, repo_path: str) -> bool:
    """
    Rollback a previously applied patch.
    
    Args:
        patch: Patch to rollback
        repo_path: Path to the repository
        
    Returns:
        True if the patch was rolled back successfully, False otherwise
    """
    logger.info(f"Rolling back patch for {patch.file_path}")
    
    try:
        # Check if patch can be rolled back
        if not patch.rollback_available or not patch.rollback_content:
            logger.error("Patch cannot be rolled back")
            return False
            
        # Construct full file path
        file_path = os.path.join(repo_path, patch.file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Read current content
        with open(file_path, "r", encoding="utf-8") as f:
            current_content = f.read()
            
        # Verify that the current content matches the expected modified content
        if current_content != patch.modified_content:
            logger.error(f"File content has changed since patch was applied")
            return False
            
        # Apply the rollback
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(patch.rollback_content)
            
        # Verify the rollback was applied correctly
        with open(file_path, "r", encoding="utf-8") as f:
            rolled_back_content = f.read()
            
        if rolled_back_content != patch.rollback_content:
            logger.error("Rollback was not applied correctly")
            # Restore to modified content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current_content)
            return False
            
        # Update patch status
        patch.applied = False
        patch.rollback_available = False
        
        logger.info(f"Successfully rolled back patch for {patch.file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error rolling back patch: {e}")
        return False


def generate_diff(original_content: str, modified_content: str) -> str:
    """
    Generate a unified diff between two versions of content.
    
    Args:
        original_content: Original content
        modified_content: Modified content
        
    Returns:
        Unified diff string
    """
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        modified_content.splitlines(keepends=True),
        fromfile="original",
        tofile="modified"
    )
    
    return "".join(diff)
