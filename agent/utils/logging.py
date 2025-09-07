"""
Logging configuration for the autonomous code improvement system.
"""

import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Path to log file (optional)
    """
    # Remove default logger
    logger.remove()
    
    # Console logger
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # File logger
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
    
    # Set log level from environment if not provided
    if not log_level:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger.info(f"Logging initialized with level: {log_level}")
