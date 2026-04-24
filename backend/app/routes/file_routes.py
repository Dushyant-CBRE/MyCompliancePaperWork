from fastapi import APIRouter, File, UploadFile
from typing import List

from app.services.file_service import (
    list_compliance_files,
    read_compliance_file,
    save_compliance_file,
)

router = APIRouter(prefix="/compliances", tags=["Compliance Files"])


@router.post("/upload", status_code=201)
async def upload_compliance_file(file: UploadFile = File(...)):
    """Upload a compliance sheet (.csv, .xlsx, or .pdf) to the work directory."""
    filename = save_compliance_file(file)
    return {"message": "File uploaded successfully.", "filename": filename}


@router.get("/", response_model=List[str])
def list_uploaded_files():
    """List all compliance files currently stored in the work directory."""
    return list_compliance_files()


@router.get("/{filename}")
def get_compliance_file(filename: str):
    """Read any uploaded compliance file (.csv, .xlsx, or .pdf) and return its content."""
    return read_compliance_file(filename)
