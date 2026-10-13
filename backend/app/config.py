from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Legal Contract Analysis Engine"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # AI / LLM Configuration
    # Options: "openai", "azure_openai", "mock"
    LLM_PROVIDER: str = Field(default="openai", description="Active LLM provider")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Azure OpenAI Configuration (optional)
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./storage/legal_contracts.db"

    # Vector Storage
    CHROMA_PERSIST_DIRECTORY: str = "./storage/chroma_db"

    # File Storage
    UPLOAD_DIRECTORY: str = "./storage/uploads"
    MAX_FILE_SIZE_MB: int = 25

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Initialize global settings singleton
settings = Settings()

# Ensure critical storage directories exist
Path(settings.UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
Path("./storage").mkdir(parents=True, exist_ok=True)
