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
        extra="ignore",
    )

    # ── Azure OpenAI LLM (via WSO2 OAuth2 Proxy) ─────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = "wso2-oauth2"  # Not used directly, auth via WSO2
    azure_openai_api_version: str = "2024-10-01-preview"
    azure_openai_deployment_id: str = ""

    # ── WSO2 OAuth2 Client Credentials ───────────────────────────────────────
    wso2_auth_url: str = ""
    wso2_client_id: str = ""
    wso2_client_secret: str = ""

    # ── Azure Storage (Blob + Table) ─────────────────────────────────────────
    azure_storage_connection_string: str = ""
    azure_blob_container_name: str = "mypapercompliance"
    azure_table_name: str = "MyPaperCompliance"
    azure_audit_table_name: str = "MyPaperComplianceAudit"

    # ── Field Extraction Configuration ───────────────────────────────────────
    field_config_path: str = "data/field_extraction_config.yaml"

    # ── Processing settings ──────────────────────────────────────────────────
    confidence_auto_approve_threshold: float = 85.0
    confidence_manual_review_threshold: float = 60.0

    # Confidence weight split (must sum to 1.0)
    weight_extraction: float = 0.30
    weight_validation: float = 0.30
    weight_remedial: float = 0.40

    # LLM settings
    llm_temperature: float = 0.2
    llm_max_retries: int = 2

    # ── App ──────────────────────────────────────────────────────────────────
    app_title: str = "My Compliance Paperwork API"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
