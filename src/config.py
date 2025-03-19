from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DocParse API"
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/docparse"
    
    # Vector Store
    VECTOR_STORE_HOST: str = "vector-db"
    VECTOR_STORE_PORT: int = 8000
    
    # File Storage
    UPLOAD_DIR: str = "data/uploads"
    
    # PDF Processing
    MAX_PDF_SIZE_MB: int = 10
    SUPPORTED_PDF_VERSIONS: list[str] = ["1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7"]
    
    # Text Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOCUMENT: int = 1000
    
    # Vector Processing
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    BATCH_SIZE: int = 32
    
    # OCR Settings
    OCR_LANGUAGE: str = "eng"
    OCR_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 