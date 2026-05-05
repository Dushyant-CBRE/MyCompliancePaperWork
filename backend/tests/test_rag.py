"""Quick smoke test for the RAG Q&A pipeline (no Azure storage needed)."""
import sys
sys.path.insert(0, ".")

from backend.services.pdf_extractor import extract_text_from_pdf
from backend.services.rag_service import answer_question, chunk_document, retrieve_relevant_chunks

PDF = r"C:\Users\DGaur\Downloads\JL - Nottingham - L3 goods lift shop floor - LFM 3968 - JLP 0006 80617.pdf"

print("Extracting PDF text...")
with open(PDF, "rb") as f:
    text = extract_text_from_pdf(f.read())
print(f"  {len(text):,} characters extracted\n")

# ── Chunking ──────────────────────────────────────────────────────────────────
chunks = chunk_document(text)
print(f"Document split into {len(chunks)} paragraph chunks:")
for c in chunks:
    print(f"  [{c['index']}] {c['text'][:80].replace(chr(10),' ')}...")
print()

QUESTIONS = [
    "What critical issues were found with the door?",
    "Who carried out the inspection and when?",
    "What is the overall outcome of the inspection?",
    "What are the door's opening and closing times?",
]

for q in QUESTIONS:
    print(f"{'='*70}")
    print(f"Q: {q}")
    hits = retrieve_relevant_chunks(chunks, q, top_k=3)
    print(f"Top retrieved chunks: {[h.chunk_index for h in hits]} (scores: {[h.relevance_score for h in hits]})")
    result = answer_question("test-doc", q, text)
    print(f"A: {result.answer}")
    print(f"Sources cited: {len(result.sources)}")
    print()
