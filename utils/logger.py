"""
Logging configuration for the Multi-Model AI API Integration System.
Uses loguru for enhanced logging features.
"""
import os
import sys
import logging
from pathlib import Path
from loguru import logger

from config import get_settings

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class InterceptHandler(logging.Handler):
    """
    Handler to intercept standard library logging and redirect to loguru
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where this was logged
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """
    Configure logging for the application
    """
    settings = get_settings()
    
    # Remove default handlers
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler for errors and above
    logger.add(
        LOG_DIR / "errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="1 month",
        compression="zip"
    )
    
    # Add file handler for all logs in production, info+ in development
    min_level = "INFO" if settings.app_env == "development" else "DEBUG"
    logger.add(
        LOG_DIR / "app.log",
        level=min_level,
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # List of standard library loggers to intercept
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
    
    logger.info(f"Logging configured with level: {settings.log_level}")
    return logger