import csv
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def _safe_filename(filename: str) -> str:
    """Strip directory components to prevent path traversal."""
    return Path(filename).name


def save_compliance_file(file: UploadFile) -> str:
    """Save an uploaded compliance sheet to the upload directory.

    Returns the sanitised filename on success.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    safe_name = _safe_filename(file.filename)
    ext = Path(safe_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Only .csv, .xlsx, and .pdf are accepted.",
        )

    content = file.file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the maximum allowed size of 10 MB.",
        )

    dest = _ensure_upload_dir() / safe_name
    dest.write_bytes(content)

    return safe_name


def read_compliance_file(filename: str):
    """Read a previously uploaded compliance file and return its content.

    - .csv / .xlsx: returns {filename, total_rows, rows}
    - .pdf:         returns {filename, total_pages, pages}
    """
    safe_name = _safe_filename(filename)
    file_path = _ensure_upload_dir() / safe_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{safe_name}' not found in the upload directory.",
        )

    ext = file_path.suffix.lower()

    if ext == ".csv":
        rows = _read_csv(file_path)
        return {"filename": safe_name, "total_rows": len(rows), "rows": rows}
    elif ext == ".xlsx":
        rows = _read_xlsx(file_path)
        return {"filename": safe_name, "total_rows": len(rows), "rows": rows}
    elif ext == ".pdf":
        return _read_pdf(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")


def list_compliance_files() -> List[str]:
    """Return names of all compliance files currently in the upload directory."""
    upload_dir = _ensure_upload_dir()
    return [
        f.name
        for f in upload_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]



# ---------------------------------------------------------------------------
# Internal readers
# ---------------------------------------------------------------------------

def _read_csv(file_path: Path) -> List[dict]:
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _read_pdf(file_path: Path) -> dict:
    try:
        import pypdf  # optional dependency
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="pypdf is required to read PDF files. Install it with: pip install pypdf",
        )

    pages = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for i, page in enumerate(reader.pages):
            pages.append({"page": i + 1, "text": page.extract_text() or ""})

    return {
        "filename": file_path.name,
        "total_pages": len(pages),
        "pages": pages,
    }


def _read_xlsx(file_path: Path) -> List[dict]:
    try:
        import openpyxl  # optional dependency
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl is required to read .xlsx files. Install it with: pip install openpyxl",
        )

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    headers = [
        str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows[0])
    ]
    return [dict(zip(headers, row)) for row in rows[1:]]
