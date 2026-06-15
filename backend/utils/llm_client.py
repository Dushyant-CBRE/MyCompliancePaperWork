"""
LLM client using Azure OpenAI via WSO2 OAuth2 Proxy.

Authenticates via WSO2 (client credentials flow) and uses the resulting token
to make Azure OpenAI API calls through the corporate proxy.
"""
from __future__ import annotations

import json
import logging
import time
from functools import lru_cache
from types import SimpleNamespace

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """
    Azure OpenAI client that authenticates via WSO2 OAuth2 proxy.
    
    Flow:
    1. Exchange CLIENT_ID + CLIENT_SECRET with WSO2 for access token
    2. Use token to make Azure OpenAI API calls through WSO2 proxy
    """

    def __init__(self) -> None:
        settings = get_settings()
        
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not configured")
        if not settings.wso2_client_id or not settings.wso2_client_secret:
            raise ValueError("WSO2_CLIENT_ID or WSO2_CLIENT_SECRET not configured")
        if not settings.azure_openai_deployment_id:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_ID not configured")

        self._endpoint = settings.azure_openai_endpoint.rstrip("/")
        self._deployment_id = settings.azure_openai_deployment_id
        self._api_version = settings.azure_openai_api_version
        self._max_retries = settings.llm_max_retries
        
        # WSO2 OAuth2 settings
        self._wso2_auth_url = settings.wso2_auth_url
        self._wso2_client_id = settings.wso2_client_id
        self._wso2_client_secret = settings.wso2_client_secret
        
        # Token cache
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

        self.chat = _ChatResource(_ChatCompletions(
            self._endpoint,
            self._deployment_id,
            self._api_version,
            self._max_retries,
            self._get_access_token,
        ))

    def _get_access_token(self) -> str:
        """
        Get a valid access token from WSO2, using cached token if not expired.
        """
        now = time.time()
        
        # Return cached token if still valid (with 30s buffer)
        if self._access_token and now < (self._token_expires_at - 30):
            return self._access_token

        # Request new token from WSO2
        logger.info("Requesting new access token from WSO2")
        
        try:
            response = httpx.post(
                self._wso2_auth_url,
                auth=(self._wso2_client_id, self._wso2_client_secret),
                data={"grant_type": "client_credentials"},
                verify=False,  # Required for corporate SSL
            )
            response.raise_for_status()
        except Exception as exc:
            logger.error(f"WSO2 token request failed: {exc}")
            raise

        data = response.json()
        self._access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        self._token_expires_at = now + expires_in

        logger.debug(f"Got new token, expires in {expires_in}s")
        return self._access_token


class _ChatCompletions:
    """Chat completions wrapper that uses WSO2-authenticated Azure OpenAI calls."""

    def __init__(self, endpoint: str, deployment_id: str, api_version: str, max_retries: int, get_token_fn) -> None:
        self._endpoint = endpoint
        self._deployment_id = deployment_id
        self._api_version = api_version
        self._max_retries = max_retries
        self._get_token_fn = get_token_fn

    def create(self, model: str, messages: list[dict], **kwargs) -> SimpleNamespace:
        """
        Create a chat completion using Azure OpenAI via WSO2 proxy.

        Parameters:
            model: Model name (ignored, deployment_id used instead)
            messages: List of message dicts with role and content
            **kwargs: Additional parameters (temperature, tools, tool_choice, etc.)

        Returns:
            SimpleNamespace with standard completion response structure
        """
        # Build the URL for Azure OpenAI (via WSO2 proxy)
        url = (
            f"{self._endpoint}/openai/deployments/{self._deployment_id}/"
            f"chat/completions?api-version={self._api_version}"
        )

        # Prepare request body
        body = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_completion_tokens", 4096),
        }

        # Add tools if provided
        if kwargs.get("tools"):
            body["tools"] = kwargs["tools"]
            if kwargs.get("tool_choice"):
                body["tool_choice"] = kwargs["tool_choice"]

        # Retry logic for rate limits and transient errors
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                access_token = self._get_token_fn()
                
                response = httpx.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    verify=False,  # Required for corporate SSL
                    timeout=60.0,
                )
                response.raise_for_status()
                
                return self._wrap_response(response.json())
            
            except Exception as exc:
                exc_str = str(exc)
                # Check if error is retryable
                is_retryable = (
                    "429" in exc_str or "rate_limit" in exc_str.lower() or
                    "503" in exc_str or "overloaded" in exc_str.lower() or
                    "timeout" in exc_str.lower()
                )

                if is_retryable and attempt < self._max_retries - 1:
                    delay = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        f"Retryable error (attempt {attempt + 1}/{self._max_retries}) – "
                        f"retrying in {delay}s: {exc}"
                    )
                    time.sleep(delay)
                    last_exc = exc
                else:
                    raise

        raise last_exc

    @staticmethod
    def _wrap_response(data: dict) -> SimpleNamespace:
        """Wrap Azure OpenAI response into standard SimpleNamespace format."""
        choice = data["choices"][0]
        message = choice["message"]

        tool_calls = None
        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = [
                SimpleNamespace(
                    id=tc["id"],
                    type="function",
                    function=SimpleNamespace(
                        name=tc["function"]["name"],
                        arguments=tc["function"]["arguments"],
                    ),
                )
                for tc in message["tool_calls"]
            ]

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=message.get("content"),
                        role=message["role"],
                        tool_calls=tool_calls,
                    ),
                    finish_reason=choice["finish_reason"],
                )
            ],
            model=data.get("model", "unknown"),
        )


class _ChatResource:
    def __init__(self, completions: _ChatCompletions) -> None:
        self.completions = completions


@lru_cache(maxsize=1)
def get_llm_client() -> AzureOpenAIClient:
    """Get or create the Azure OpenAI client authenticated via WSO2 (cached singleton)."""
    return AzureOpenAIClient()
