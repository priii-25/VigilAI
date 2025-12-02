"""
Logging configuration using Loguru
"""
import sys
from loguru import logger
from src.core.config import settings


def setup_logging():
    """Configure application logging"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
    )
    
    # File handler for all logs
    logger.add(
        "logs/vigilai_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    )
    
    # File handler for errors only
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    )
    
    return logger
