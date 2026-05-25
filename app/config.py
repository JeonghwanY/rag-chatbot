"""애플리케이션 설정. .env 파일에서 환경변수 로드."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API 키
    google_api_key: str

    # 경로
    vectorstore_dir: Path = Path("./vectorstore")
    docs_dir: Path = Path("./data/docs")

    # 모델
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "models/text-embedding-004"

    # RAG 파라미터
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 4


settings = Settings()
