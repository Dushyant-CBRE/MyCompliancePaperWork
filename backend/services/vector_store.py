"""
Vector Store – PGVector Backend
─────────────────────────────────
Stores and queries document chunk embeddings using PostgreSQL + pgvector.

Table schema (auto-created on first use):
  document_chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  TEXT NOT NULL,
    chunk_index  INT  NOT NULL,
    chunk_text   TEXT NOT NULL,
    embedding    vector(1536),
    created_at   TIMESTAMPTZ DEFAULT now()
  )

Index: IVFFlat on embedding for fast approximate nearest-neighbour search.

Usage:
    store_document_chunks(document_id, chunks, embeddings)
    search_similar_chunks(document_id, query_embedding, top_k=5)
    delete_document_chunks(document_id)
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from backend.config import get_settings
from backend.models.document import CitedChunk

logger = logging.getLogger(__name__)

_DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  TEXT NOT NULL,
    chunk_index  INT  NOT NULL,
    chunk_text   TEXT NOT NULL,
    embedding    vector(1536),
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_chunks_doc_idx
    ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS document_chunks_ivfflat_idx
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
"""


@contextmanager
def _get_conn() -> Generator:
    """Open a psycopg2 connection. Yields conn, closes on exit."""
    try:
        import psycopg2  # type: ignore
        from pgvector.psycopg2 import register_vector  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "psycopg2-binary and pgvector not installed. "
            "Run: pip install psycopg2-binary pgvector"
        ) from exc

    settings = get_settings()
    if not settings.pgvector_host:
        raise RuntimeError("PGVECTOR_HOST not configured")

    conn = psycopg2.connect(
        host=settings.pgvector_host,
        port=settings.pgvector_port,
        dbname=settings.pgvector_db,
        user=settings.pgvector_user,
        password=settings.pgvector_password,
        connect_timeout=10,
        sslmode="require",
    )
    register_vector(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema() -> None:
    """Create the document_chunks table and indexes if they don't exist."""
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_DDL)
        logger.info("PGVector schema ensured")
    except Exception as exc:
        logger.warning("PGVector schema setup failed (RAG disabled): %s", exc)


def store_document_chunks(
    document_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    """
    Upsert chunks for a document.
    Deletes any existing rows for this document_id first (idempotent).

    Parameters
    ----------
    chunks      : list of {"index": int, "text": str}
    embeddings  : parallel list of 1536-dim float vectors
    """
    if not chunks:
        return

    import numpy as np  # type: ignore

    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                # Remove old chunks for this document (re-process idempotency)
                cur.execute(
                    "DELETE FROM document_chunks WHERE document_id = %s",
                    (document_id,),
                )
                # Bulk insert
                rows = [
                    (document_id, chunk["index"], chunk["text"], np.array(emb))
                    for chunk, emb in zip(chunks, embeddings)
                ]
                cur.executemany(
                    """
                    INSERT INTO document_chunks
                        (document_id, chunk_index, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    rows,
                )
        logger.info(
            "Stored %d chunks for document %s in PGVector", len(chunks), document_id
        )
    except Exception as exc:
        logger.warning(
            "PGVector chunk storage failed for %s (RAG degraded): %s",
            document_id, exc,
        )


def search_similar_chunks(
    document_id: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[CitedChunk]:
    """
    Find the top-k most similar chunks for a document using cosine similarity.

    Returns an empty list (falls back to keyword RAG) if PGVector is unavailable.
    """
    import numpy as np  # type: ignore

    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT chunk_index, chunk_text,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM   document_chunks
                    WHERE  document_id = %s
                    ORDER  BY embedding <=> %s::vector
                    LIMIT  %s
                    """,
                    (
                        np.array(query_embedding),
                        document_id,
                        np.array(query_embedding),
                        top_k,
                    ),
                )
                rows = cur.fetchall()

        return [
            CitedChunk(
                chunk_index=row[0],
                text=row[1],
                relevance_score=round(float(row[2]), 4),
            )
            for row in rows
        ]

    except Exception as exc:
        logger.warning(
            "PGVector search failed for %s (falling back to keyword): %s",
            document_id, exc,
        )
        return []


def delete_document_chunks(document_id: str) -> None:
    """Remove all stored chunks for a document (called on document deletion)."""
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM document_chunks WHERE document_id = %s",
                    (document_id,),
                )
        logger.info("Deleted PGVector chunks for document %s", document_id)
    except Exception as exc:
        logger.warning("PGVector delete failed for %s: %s", document_id, exc)
