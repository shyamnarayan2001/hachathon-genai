from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///database/retail.db")
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # LLM Settings
    PRIMARY_MODEL: str = "mixtral-8x7b-32768"
    FALLBACK_MODEL: str = "gpt-4"
    TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"