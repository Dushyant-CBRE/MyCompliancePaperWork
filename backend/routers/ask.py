"""
Reviewer Q&A Router
────────────────────
POST /api/documents/{document_id}/ask

Allows a compliance reviewer to ask free-text questions about a specific
document and receive answers grounded in the original document text,
with cited source passages shown so the reviewer can verify the answer.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.models.document import AskRequest, AskResponse
from backend.services.rag_service import answer_question
from backend.services.storage_service import get_document_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["ask"])


@router.post("/{document_id}/ask", response_model=AskResponse)
def ask_document(document_id: str, request: AskRequest) -> AskResponse:
    """
    Ask a question about a specific document.

    The answer is generated using Retrieval-Augmented Generation:
    relevant passages are retrieved from the stored document text and
    passed to the LLM as grounding context.  The response includes
    both the answer and the cited source passages so the reviewer
    can verify the AI's reasoning against the original document.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    document_text = get_document_text(document_id)
    if document_text is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Document text not found for document_id={document_id!r}. "
                "The document may not have been processed yet, or was uploaded "
                "before text storage was enabled."
            ),
        )

    logger.info("Q&A request: document_id=%s question=%r", document_id, request.question)
    return answer_question(
        document_id=document_id,
        question=request.question.strip(),
        document_text=document_text,
    )
