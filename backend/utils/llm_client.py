"""
LLM client using the CBRE WSO2 API Gateway proxy for Azure OpenAI.

Bypasses the openai SDK entirely and uses plain httpx, since the gateway
requires Bearer token auth (not api-key) and the SDK URL construction
conflicts with WSO2 routing.

Auth flow:
  1. POST {WSO2_AUTH_URL} with grant_type=client_credentials → Bearer token
  2. Token is cached and refreshed automatically before expiry.
  3. Every outbound request carries  Authorization: Bearer <token>
"""
from __future__ import annotations

import threading
import time
import json
from types import SimpleNamespace
from functools import lru_cache

import httpx

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
        self._expires_at = time.monotonic() + payload.get("expires_in", 3600) - 60


class _ChatCompletions:
    """Minimal chat.completions.create() compatible with the openai SDK interface."""

    def __init__(self, base_url: str, api_version: str, token_mgr: _WSO2TokenManager) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_version = api_version
        self._token_mgr = token_mgr

    def create(self, model: str, messages: list, **kwargs) -> SimpleNamespace:
        url = (
            f"{self._base_url}/openai/deployments/{model}"
            f"/chat/completions?api-version={self._api_version}"
        )
        body: dict = {"messages": messages}
        # Pass through supported kwargs
        for key in ("temperature", "response_format", "max_completion_tokens", "top_p", "tools", "tool_choice"):
            if key in kwargs:
                body[key] = kwargs[key]

        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self._token_mgr.get_token()}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        # Wrap response to match openai SDK shape: r.choices[0].message.content
        choices = []
        for c in data.get("choices", []):
            msg_data = c.get("message", {})
            # Parse tool_calls if present (agentic tool-use response)
            tool_calls_raw = msg_data.get("tool_calls")
            tool_calls = None
            if tool_calls_raw:
                tool_calls = [
                    SimpleNamespace(
                        id=tc.get("id"),
                        type=tc.get("type", "function"),
                        function=SimpleNamespace(
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"],
                        ),
                    )
                    for tc in tool_calls_raw
                ]
            msg = SimpleNamespace(
                content=msg_data.get("content", ""),
                role=msg_data.get("role", "assistant"),
                tool_calls=tool_calls,
            )
            choices.append(SimpleNamespace(message=msg, finish_reason=c.get("finish_reason")))
        return SimpleNamespace(choices=choices, model=data.get("model", model))


class _ChatResource:
    def __init__(self, completions: _ChatCompletions) -> None:
        self.completions = completions


class CBREProxyClient:
    """Drop-in replacement for openai.AzureOpenAI using direct httpx calls."""

    def __init__(self) -> None:
        settings = get_settings()
        token_mgr = _WSO2TokenManager(
            token_url=settings.wso2_auth_url,
            client_id=settings.wso2_client_id,
            client_secret=settings.wso2_client_secret,
        )
        completions = _ChatCompletions(
            base_url=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            token_mgr=token_mgr,
        )
        self.chat = _ChatResource(completions)


@lru_cache(maxsize=1)
def get_llm_client() -> CBREProxyClient:
    return CBREProxyClient()
