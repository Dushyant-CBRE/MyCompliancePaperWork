"""
LLM client using the CBRE WSO2 API Gateway proxy for Azure OpenAI.

Auth flow:
  1. POST {WSO2_AUTH_URL} with grant_type=client_credentials → Bearer token
  2. Token is cached and refreshed automatically before expiry.
  3. Every outbound request carries  Authorization: Bearer <token>
"""
from __future__ import annotations

import threading
import time
from functools import lru_cache

import httpx
import openai

from backend.config import get_settings


class _WSO2TokenManager:
    """Thread-safe OAuth2 client-credentials token cache."""

    def __init__(self, token_url: str, client_id: str, client_secret: str) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str = ""
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        with self._lock:
            if not self._token or time.monotonic() >= self._expires_at:
                self._refresh()
        return self._token

    def _refresh(self) -> None:
        resp = httpx.post(
            self._token_url,
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._client_secret),
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        # Refresh 60 seconds before the token actually expires
        self._expires_at = time.monotonic() + payload.get("expires_in", 3600) - 60


@lru_cache(maxsize=1)
def get_llm_client() -> openai.AzureOpenAI:
    settings = get_settings()
    token_mgr = _WSO2TokenManager(
        token_url=settings.wso2_auth_url,
        client_id=settings.wso2_client_id,
        client_secret=settings.wso2_client_secret,
    )

    def _inject_bearer(request: httpx.Request) -> None:
        request.headers["Authorization"] = f"Bearer {token_mgr.get_token()}"

    http_client = httpx.Client(event_hooks={"request": [_inject_bearer]})

    return openai.AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key="placeholder",  # Required by SDK; real auth is the Bearer token above
        api_version=settings.azure_openai_api_version,
        http_client=http_client,
    )
