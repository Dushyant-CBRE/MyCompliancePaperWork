"""
RAG (Retrieval-Augmented Generation) Service
─────────────────────────────────────────────
Enables reviewers to ask free-form questions about a specific document and
receive answers grounded in the original text, with cited source passages.

No vector database or external framework required.  Retrieval is done via
keyword overlap (TF-IDF-style) which is accurate enough for the short
compliance documents we process (typically < 5 pages / 5,000 tokens).

Flow
────
  1. chunk_document()       – split text into overlapping paragraphs
  2. retrieve_relevant_chunks() – rank by keyword overlap, return top-k
  3. answer_question()      – send question + chunks to LLM, parse answer
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from math import log

from backend.config import get_settings
from backend.models.document import AskResponse, CitedChunk
from backend.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ── Chunking ──────────────────────────────────────────────────────────────────

_MIN_CHUNK_LEN = 30   # discard very short paragraphs


def chunk_document(text: str) -> list[dict]:
    """
    Split document text into paragraph-level chunks.

    Returns a list of dicts:
      {"index": int, "text": str}
    """
    # Split on blank lines or line breaks before/after bullet-like patterns
    raw_chunks = re.split(r"\n{2,}", text.strip())
    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunk = chunk.strip()
        if len(chunk) >= _MIN_CHUNK_LEN:
            chunks.append({"index": i, "text": chunk})
    return chunks


# ── Retrieval ─────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Lowercase, remove punctuation, split into tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "was", "are", "were", "be", "been", "has", "have",
    "had", "this", "that", "it", "its", "by", "from", "as", "not", "no",
    "what", "when", "where", "who", "which", "how", "does", "do", "did",
}


def retrieve_relevant_chunks(
    chunks: list[dict],
    question: str,
    top_k: int = 5,
) -> list[CitedChunk]:
    """
    Score each chunk by TF-IDF-inspired keyword overlap against the question.
    Falls back to exact-token substring scan when all TF-IDF scores are zero.
    Returns the top-k chunks sorted by relevance descending.
    """
    if not chunks:
        return []

    q_tokens = [t for t in _tokenise(question) if t not in _STOP_WORDS]
    if not q_tokens:
        return [
            CitedChunk(chunk_index=c["index"], text=c["text"], relevance_score=0.0)
            for c in chunks[:top_k]
        ]

    q_set = set(q_tokens)
    n = len(chunks)

    # Document frequency for IDF
    df: Counter = Counter()
    chunk_tokens_list: list[list[str]] = []
    for chunk in chunks:
        tokens = [t for t in _tokenise(chunk["text"]) if t not in _STOP_WORDS]
        chunk_tokens_list.append(tokens)
        df.update(set(tokens))

    scored: list[tuple[float, dict]] = []
    for chunk, tokens in zip(chunks, chunk_tokens_list):
        if not tokens:
            continue
        tf = Counter(tokens)
        score = 0.0
        for term in q_set:
            if term in tf:
                idf = log((n + 1) / (df[term] + 1)) + 1
                score += (tf[term] / len(tokens)) * idf
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If all scores are zero, fall back to substring scan: find chunks that
    # contain at least one query token as a substring (case-insensitive)
    if not scored or scored[0][0] == 0.0:
        q_lower = question.lower()
        fallback: list[tuple[float, dict]] = []
        for chunk in chunks:
            text_lower = chunk["text"].lower()
            # Count how many query tokens appear as substrings
            hits = sum(1 for t in q_tokens if t in text_lower)
            if hits > 0:
                fallback.append((hits / len(q_tokens), chunk))
        if fallback:
            fallback.sort(key=lambda x: x[0], reverse=True)
            scored = fallback
        else:
            # Last resort: first top_k chunks
            scored = [(0.0, c) for c in chunks[:top_k]]

    results = []
    for s, chunk in scored[:top_k]:
        results.append(
            CitedChunk(
                chunk_index=chunk["index"],
                text=chunk["text"],
                relevance_score=round(min(s, 1.0), 4),
            )
        )
    return results


# ── Answer generation ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a compliance document review assistant.
You will be given passages extracted from a PPM (Planned Preventive Maintenance)
compliance document, followed by a reviewer's question about that document.

Answer the question using ONLY information found in the provided passages.
If the answer is not in the passages, say "I could not find that information in \
the document."

Be concise and precise. Quote exact values or phrases from the passages when \
they are relevant to the answer.
"""

# Documents shorter than this threshold are sent in full to the LLM.
# Typical compliance PDFs (1-5 pages) fall well below this.
_FULL_TEXT_THRESHOLD_CHARS = 8_000



def answer_question(
    document_id: str,
    question: str,
    document_text: str,
) -> AskResponse:
    """
    RAG pipeline — vector-first with keyword fallback:

    1. Embed the question using Azure AI Foundry text-embedding-3-small
    2. Search PGVector for the top-5 semantically similar chunks
    3. If PGVector unavailable or no results, fall back to TF-IDF keyword search
    4. Short documents (< 8k chars): send full text directly (no retrieval)

    Returns the answer + cited source passages with similarity scores.
    """
    settings = get_settings()
    client = get_llm_client()

    if len(document_text) <= _FULL_TEXT_THRESHOLD_CHARS:
        # Full-text mode — no retrieval needed
        context = document_text
        sources: list[CitedChunk] = [
            CitedChunk(chunk_index=0, text=document_text, relevance_score=1.0)
        ]
        logger.info(
            "RAG full-text mode: document_id=%s question=%r chars=%d",
            document_id, question, len(document_text),
        )
    else:
        chunks = chunk_document(document_text)

        # ── Try vector search first ───────────────────────────────────────────
        sources = []
        try:
            from backend.services.embedding_service import embed_single
            from backend.services.vector_store import search_similar_chunks

            query_vec = embed_single(question)
            sources = search_similar_chunks(document_id, query_vec, top_k=5)
            if sources:
                logger.info(
                    "RAG vector search: document_id=%s question=%r top_similarity=%.3f",
                    document_id, question, sources[0].relevance_score,
                )
        except Exception as exc:
            logger.warning("Vector search failed, falling back to keyword: %s", exc)

        # ── Keyword fallback if vector search returned nothing ────────────────
        if not sources:
            sources = retrieve_relevant_chunks(chunks, question, top_k=5)
            logger.info(
                "RAG keyword fallback: document_id=%s question=%r chunks=%d",
                document_id, question, len(sources),
            )

        context_parts = [f"[Passage {i+1}]\n{s.text}" for i, s in enumerate(sources)]
        context = "\n\n".join(context_parts)

    user_message = (
        f"Document text:\n\n{context}\n\n"
        f"Reviewer question: {question}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_primary,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
        answer = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.exception("RAG answer generation failed: %s", exc)
        answer = f"An error occurred while generating the answer: {exc}"

    return AskResponse(
        question=question,
        answer=answer,
        sources=sources,
        document_id=document_id,
    )
