"""
Configuration management for the Multimodal RAG System
"""
import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    app_name: str = "Multimodal RAG System"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/multimodal_rag",
        env="DATABASE_URL"
    )
    
    # Vector Database Settings
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    vector_db_type: str = Field(default="chromadb", env="VECTOR_DB_TYPE")  # chromadb or faiss
    
    # Embedding Model Settings
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL_NAME"
    )
    embedding_dim: int = Field(default=384, env="EMBEDDING_DIM")
    
    # Ollama Settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=120, env="OLLAMA_TIMEOUT")
    
    # File Upload Settings
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    allowed_extensions: List[str] = Field(default=[".pdf"], env="ALLOWED_EXTENSIONS")
    upload_directory: str = Field(default="./data/uploads", env="UPLOAD_DIRECTORY")
    
    # Processing Settings
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    max_chunks_per_query: int = Field(default=5, env="MAX_CHUNKS_PER_QUERY")
    
    # Retrieval Settings
    retrieval_k: int = Field(default=10, env="RETRIEVAL_K")
    rerank_k: int = Field(default=5, env="RERANK_K")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Scoring Weights
    semantic_weight: float = Field(default=0.6, env="SEMANTIC_WEIGHT")
    lexical_weight: float = Field(default=0.3, env="LEXICAL_WEIGHT")
    table_boost: float = Field(default=1.2, env="TABLE_BOOST")
    
    # Security Settings
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Redis Settings (for background tasks)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Evaluation Settings
    evaluation_dataset_path: str = Field(
        default="./data/evaluation/test_queries.json",
        env="EVALUATION_DATASET_PATH"
    )
    target_accuracy: float = Field(default=0.98, env="TARGET_ACCURACY")
    
    @validator("upload_directory", "vector_db_path", pre=True)
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("allowed_extensions", pre=True)
    def parse_extensions(cls, v):
        """Parse comma-separated extensions"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Database configuration
DATABASE_CONFIG = {
    "url": settings.database_url,
    "echo": settings.debug,
    "future": True,
}

# Vector database configuration
VECTOR_DB_CONFIG = {
    "type": settings.vector_db_type,
    "path": settings.vector_db_path,
    "embedding_dim": settings.embedding_dim,
}

# Ollama configuration
OLLAMA_CONFIG = {
    "base_url": settings.ollama_base_url,
    "model": settings.ollama_model,
    "timeout": settings.ollama_timeout,
}

# Processing configuration
PROCESSING_CONFIG = {
    "chunk_size": settings.chunk_size,
    "chunk_overlap": settings.chunk_overlap,
    "max_chunks_per_query": settings.max_chunks_per_query,
}

# Retrieval configuration
RETRIEVAL_CONFIG = {
    "k": settings.retrieval_k,
    "rerank_k": settings.rerank_k,
    "similarity_threshold": settings.similarity_threshold,
    "semantic_weight": settings.semantic_weight,
    "lexical_weight": settings.lexical_weight,
    "table_boost": settings.table_boost,
}

# Security configuration
SECURITY_CONFIG = {
    "secret_key": settings.secret_key,
    "algorithm": settings.algorithm,
    "access_token_expire_minutes": settings.access_token_expire_minutes,
} 