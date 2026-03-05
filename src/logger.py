"""
Logging configuration for the Clinical Note Processing API.

This module provides centralized logging configuration with:
- Console and file handlers
- Structured log format with timestamps
- Different log levels for development and production
- Request ID tracking for debugging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class LogConfig:
    """
    Centralized logging configuration.
    
    Attributes:
        LOG_LEVEL: Default logging level (INFO for production, DEBUG for development)
        LOG_FORMAT: Standard format for log messages
        LOG_DIR: Directory for log files
    """
    
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / f"clinical_api_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str, level: int = None) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        level: Logging level (defaults to LogConfig.LOG_LEVEL)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level or LogConfig.LOG_LEVEL)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(LogConfig.LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # File handler
    LogConfig.LOG_DIR.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(LogConfig.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(LogConfig.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_api_request(logger: logging.Logger, endpoint: str, **kwargs):
    """
    Log API request details in a structured format.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint being called
        **kwargs: Additional context (e.g., note_length, question, etc.)
    """
    context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"API Request: {endpoint} | {context}")


def log_api_response(logger: logging.Logger, endpoint: str, status: str, duration_ms: float = None, **kwargs):
    """
    Log API response details in a structured format.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint that was called
        status: Response status (success/error)
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context (e.g., error_message, entities_found, etc.)
    """
    context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    duration_str = f" | duration={duration_ms}ms" if duration_ms else ""
    logger.info(f"API Response: {endpoint} | status={status}{duration_str} | {context}")


def log_llm_call(logger: logging.Logger, operation: str, model: str, tokens: int = None, **kwargs):
    """
    Log LLM API call details for debugging and cost tracking.
    
    Args:
        logger: Logger instance
        operation: Type of operation (extract/query)
        model: Model name
        tokens: Token count (if available)
        **kwargs: Additional context
    """
    context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    tokens_str = f" | tokens={tokens}" if tokens else ""
    logger.debug(f"LLM Call: {operation} | model={model}{tokens_str} | {context}")
