from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:9b"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024
    OLLAMA_TIMEOUT_SECONDS: float = 300.0
    RETRIEVAL_LIMIT: int = 5
    RETRIEVAL_THRESHOLD: float = 0.55
    INGREDIENT_RETRIEVAL_THRESHOLD: float = 0.40
    RETRIEVAL_FOLLOWUP_THRESHOLD: float = 0.35
    OLLAMA_MAX_OUTPUT_TOKENS: int = 512

    THECOCKTAILDB_BASE_URL: str = "https://www.thecocktaildb.com/api/json/v1/1"
    THECOCKTAILDB_TIMEOUT_SECONDS: float = 20.0
    THECOCKTAILDB_MAX_ITEMS: int = 100
    THECOCKTAILDB_INGREDIENT_MAX_ITEMS: int = 3
    ADMIN_INGEST_KEY: str | None = None

    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200
    SUPABASE_TIMEOUT_SECONDS: float = 20.0

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings(_env_file="../.env")
