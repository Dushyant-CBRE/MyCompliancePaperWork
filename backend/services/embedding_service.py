"""
Embedding Service
──────────────────
Generates vector embeddings using Azure AI Foundry text-embedding-3-small.

Uses the Azure OpenAI-compatible REST endpoint directly via httpx so no
additional SDK is needed beyond what is already installed.

Dimension: 1536 (text-embedding-3-small default)
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536   # text-embedding-3-small output dimension
_BATCH_SIZE   = 16     # max texts per API call


def _get_client() -> httpx.Client:
    """Return a shared httpx client (no SSL verify for corporate proxy)."""
    return httpx.Client(verify=False, timeout=60.0)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings.  Returns a parallel list of 1536-dim float vectors.
    Batches calls to stay within the API's input limit.

    Raises on API error so callers can handle gracefully.
    """
    settings = get_settings()
    if not settings.azure_embedding_endpoint or not settings.azure_embedding_key:
        raise RuntimeError("Azure embedding endpoint/key not configured")

    # Azure OpenAI-compatible path:
    # POST {endpoint}/openai/deployments/{deployment}/embeddings?api-version=2024-02-01
    url = (
        f"{settings.azure_embedding_endpoint.rstrip('/')}"
        f"/openai/deployments/{settings.azure_embedding_deployment}"
        f"/embeddings?api-version=2024-02-01"
    )
    headers = {
        "api-key": settings.azure_embedding_key,
        "Content-Type": "application/json",
    }

    all_embeddings: list[list[float]] = []

    with _get_client() as client:
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            payload = {"input": batch, "model": settings.azure_embedding_deployment}

            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

            data = resp.json()
            # Sort by index to preserve order
            items = sorted(data["data"], key=lambda x: x["index"])
            all_embeddings.extend(item["embedding"] for item in items)

    logger.debug("Embedded %d texts → %d vectors", len(texts), len(all_embeddings))
    return all_embeddings


def embed_single(text: str) -> list[float]:
    """Convenience wrapper to embed one string."""
    return embed_texts([text])[0]
