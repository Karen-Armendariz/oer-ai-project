from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openalg_api_key: str | None = Field(default=None, validation_alias="OPENALG_API_KEY")
    chroma_dir: str = Field(default=str(PROJECT_ROOT / "data" / "chroma_db"))
    max_results: int = Field(default=5, validation_alias="OER_MAX_RESULTS")
    retrieval_top_k: int = Field(default=20, validation_alias="OER_RETRIEVAL_TOP_K")
    distance_threshold: float = Field(default=1.15, validation_alias="OER_DISTANCE_THRESHOLD")
    keyword_min_overlap: int = Field(default=1, validation_alias="OER_KEYWORD_MIN_OVERLAP")
    log_level: str = Field(default="INFO", validation_alias="OER_LOG_LEVEL")
    api_title: str = Field(default="OER RAG API", validation_alias="OER_API_TITLE")
    api_version: str = Field(default="1.0.0", validation_alias="OER_API_VERSION")
    cors_origins: str = Field(
        default="",
        description="Comma-separated origins, e.g. http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )
