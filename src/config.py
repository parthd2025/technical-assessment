"""Configuration management for the Clinical Note Processing API"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
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
        """Validate required configuration"""
        if not cls.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY not found. Please set it in .env file or as an environment variable."
            )


# Validate configuration on import
Config.validate()
