from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv 

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.prod'), 
        env_file_encoding='utf-8', 
        extra='ignore'
    )
    # AWS configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    LANGSMITH_TRACING: Optional[str] = None
    LANGSMITH_ENDPOINT: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None
    # Gemini
    GOOGLE_API_KEY: Optional[str] = None
    
    #Mistral
    MISTRAL_API_KEY: Optional[str] = None
    
    # Local LLM config
    LLM_BASE_URL: str = "http://127.0.0.1:8080"
    LLM_MODEL_NAME: str = "Qwen3.5-4B"
    LLM_TEMPERATURE: float = 0.1

    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    

settings = Settings()
