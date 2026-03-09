"""Upload and batch management endpoints."""


import io
import zipfile
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.document import Batch, Document
from app.schemas.api import BatchResponse, DocumentSummary
from app.config import settings
from app.services.storage import upload_to_raw

router = APIRouter(prefix="/api/batches", tags=["upload"])

ALLOWED_MIME = set(settings.allowed_mime_types)
IMAGE_MIMES = {"application/pdf", "image/jpeg", "image/png"}


def _batch_name() -> str:
    return f"Batch_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"


@router.post("", response_model=BatchResponse)
async def upload_batch(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more files (PDF, JPEG, PNG, or a single .zip) to create a batch."""
    if not files:
        raise HTTPException(400, "No files provided")

    batch = Batch(name=_batch_name(), status="pending")
    db.add(batch)
    await db.flush()  # get batch.id assigned

    documents: list[Document] = []

    for upload_file in files:
        content = await upload_file.read()
        mime = upload_file.content_type or ""

        if mime not in ALLOWED_MIME:
            raise HTTPException(
                400,
                f"Unsupported file type: {upload_file.filename} ({mime}). "
                f"Allowed: PDF, JPEG, PNG, ZIP",
            )

        if mime == "application/zip":
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    for entry_name in zf.namelist():
                        if entry_name.endswith("/"):
                            continue
                        entry_bytes = zf.read(entry_name)
                        entry_mime = _guess_mime(entry_name)
                        if entry_mime not in IMAGE_MIMES:
                            continue
                        uri = upload_to_raw(entry_bytes, entry_name, entry_mime)
                        doc = _create_document(batch.id, entry_name, entry_mime, uri)
                        documents.append(doc)
            except zipfile.BadZipFile:
                raise HTTPException(400, f"Invalid zip file: {upload_file.filename}")
        else:
            filename = upload_file.filename or "unnamed"
            uri = upload_to_raw(content, filename, mime)
            doc = _create_document(batch.id, filename, mime, uri)
            documents.append(doc)

    if not documents:
        raise HTTPException(400, "No valid documents found in upload")

    batch.total_documents = len(documents)
    for doc in documents:
        db.add(doc)

    await db.commit()
    await db.refresh(batch)
    return batch


def _create_document(batch_id: str, filename: str, mime_type: str, gcs_raw_uri: str) -> Document:
    return Document(
        batch_id=batch_id,
        original_filename=filename,
        mime_type=mime_type,
        gcs_raw_uri=gcs_raw_uri,
        status="uploaded",
    )


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    elif lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif lower.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


@router.get("", response_model=list[BatchResponse])
async def list_batches(db: AsyncSession = Depends(get_db)):
    """List all batches ordered by creation date descending."""
    result = await db.execute(
        select(Batch).order_by(Batch.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(404, "Batch not found")
    return batch


@router.get("/{batch_id}/documents", response_model=list[DocumentSummary])
async def list_batch_documents(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document)
        .where(Document.batch_id == batch_id)
        .order_by(Document.created_at)
    )
    return result.scalars().all()
