"""
Configuration management for the Clinical Note Processing API.

This module handles all application configuration including:
- Environment variable loading
- API settings
- LLM/Groq configuration
- Default values and validation

Configuration is loaded from .env file or environment variables.
Required variables are validated on module import.
"""

import os
from dotenv import load_dotenv
from .logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = setup_logger(__name__)


class Config:
    """
    Application configuration singleton.
    
    This class loads and validates all configuration settings from
    environment variables with sensible defaults where appropriate.
    
    Environment Variables:
        APP_HOST: Host address for the API server (default: 0.0.0.0)
        APP_PORT: Port number for the API server (default: 8000)
        GROQ_API_KEY: API key for Groq LLM service (required)
        GROQ_MODEL: Groq model to use (default: llama-3.1-70b-versatile)
        LLM_TEMPERATURE: Temperature for LLM generation (default: 0)
        LLM_MAX_TOKENS_EXTRACT: Max tokens for extraction (default: 1000)
        LLM_MAX_TOKENS_QUERY: Max tokens for Q&A (default: 300)
    
    Raises:
        RuntimeError: If required configuration is missing
    
    Example:
        >>> from config import Config
        >>> print(Config.GROQ_MODEL)
        'llama-3.1-70b-versatile'
    """
    
    # API Configuration
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    
    # Groq API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))
    LLM_MAX_TOKENS_EXTRACT = int(os.getenv("LLM_MAX_TOKENS_EXTRACT", 1000))
    LLM_MAX_TOKENS_QUERY = int(os.getenv("LLM_MAX_TOKENS_QUERY", 300))
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present.
        
        Raises:
            RuntimeError: If GROQ_API_KEY is not set
        """
        logger.info("Validating configuration...")
        
        if not cls.GROQ_API_KEY:
            logger.error("GROQ_API_KEY not found in environment")
            raise RuntimeError(
                "GROQ_API_KEY not found. Please set it in .env file or as an environment variable."
            )
        
        logger.info(f"Configuration validated successfully - Model: {cls.GROQ_MODEL}, Temperature: {cls.LLM_TEMPERATURE}")
    
    @classmethod
    def get_info(cls) -> dict:
        """
        Get configuration information (excluding sensitive data).
        
        Returns:
            Dictionary with non-sensitive configuration values
        """
        return {
            "app_host": cls.APP_HOST,
            "app_port": cls.APP_PORT,
            "groq_model": cls.GROQ_MODEL,
            "llm_temperature": cls.LLM_TEMPERATURE,
            "llm_max_tokens_extract": cls.LLM_MAX_TOKENS_EXTRACT,
            "llm_max_tokens_query": cls.LLM_MAX_TOKENS_QUERY,
            "groq_api_key_set": bool(cls.GROQ_API_KEY)
        }


# Validate configuration on import
logger.info("Loading configuration...")
Config.validate()
logger.info("Configuration loaded successfully")
