"""
Logging configuration using Loguru
Enhanced with structured logging and request context support
"""
import sys
from loguru import logger
from src.core.config import settings


def setup_logging():
    """Configure application logging with structured output"""
    
    # Remove default handler
    logger.remove()
    
    # Console format with request context
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<dim>req:{extra[request_id]}</dim> | "
        "<dim>tenant:{extra[tenant_id]}</dim> - "
        "<level>{message}</level>"
    )
    
    # Simpler format for when context is missing
    simple_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Structured JSON format for production log analysis
    json_format = (
        '{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
        '"level":"{level}",'
        '"logger":"{name}",'
        '"function":"{function}",'
        '"line":{line},'
        '"request_id":"{extra[request_id]}",'
        '"tenant_id":"{extra[tenant_id]}",'
        '"correlation_id":"{extra[correlation_id]}",'
        '"user_id":"{extra[user_id]}",'
        '"message":"{message}"}}'
    )
    
    # Configure default extra values
    logger.configure(
        extra={
            "request_id": "system",
            "tenant_id": "default",
            "correlation_id": "system",
            "user_id": "system"
        }
    )
    
    # Console handler
    logger.add(
        sys.stdout,
        colorize=True,
        format=simple_format,
        level=settings.LOG_LEVEL,
        filter=lambda record: not record["extra"].get("json_only", False)
    )
    
    # File handler for all logs (human readable)
    logger.add(
        "logs/vigilai_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | req:{extra[request_id]} | tenant:{extra[tenant_id]} - {message}",
    )
    
    # JSON file handler for production log aggregation
    if settings.APP_ENV == "production":
        logger.add(
            "logs/vigilai_{time:YYYY-MM-DD}.json",
            format=json_format,
            rotation="500 MB",
            retention="30 days",
            compression="zip",
            level=settings.LOG_LEVEL,
            serialize=False  # We're formatting as JSON manually
        )
    
    # File handler for errors only
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | req:{extra[request_id]} - {message}",
    )
    
    logger.info("Logging configured", app_env=settings.APP_ENV)
    return logger


def get_logger():
    """Get configured logger instance"""
    return logger
