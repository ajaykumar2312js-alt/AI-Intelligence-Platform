from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/rag_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "meta/llama-3.3-70b-instruct"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
