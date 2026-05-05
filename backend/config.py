"""
Application configuration loaded from environment variables.
Fill in .env (copy from .env.example) before running.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Resolve .env relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Anthropic Claude via Azure AI Foundry ──────────────────────────────
    anthropic_api_key: str = ""
    anthropic_endpoint: str = "https://admv-mogidbp0-eastus2.services.ai.azure.com/anthropic/"
    anthropic_deployment: str = "claude-sonnet-4-6"

    # Keep these so existing references in agents don't crash (mapped to deployment)
    azure_openai_deployment_primary: str = "claude-sonnet-4-6"
    azure_openai_deployment_fallback: str = "claude-sonnet-4-6"

    # ── Azure Storage (Blob + Table) ─────────────────────────────────────────
    azure_storage_connection_string: str = ""
    azure_blob_container_name: str = "mypapercompliance"
    azure_table_name: str = "MyPaperCompliance"

    # ── Processing settings ──────────────────────────────────────────────────
    confidence_auto_approve_threshold: float = 85.0
    confidence_manual_review_threshold: float = 60.0

    # Confidence weight split (must sum to 1.0)
    weight_extraction: float = 0.30
    weight_validation: float = 0.30
    weight_remedial: float = 0.40

    # ── App ──────────────────────────────────────────────────────────────────
    app_title: str = "My Compliance Paperwork API"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
