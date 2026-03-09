"""Document extraction, review, and approval endpoints."""


import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.document import Document, AuditLog, Batch
from app.schemas.api import DocumentDetail, ReviewSubmission
from app.schemas.ecvi import ECVIData, ExtractionResult
from app.services.extraction import extract_from_document
from app.services.xml_generator import generate_ecvi_xml
from app.services.storage import download_file, upload_xml_to_archive

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Serve the original scanned document for viewing in the browser."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    if not doc.gcs_raw_uri:
        raise HTTPException(404, "No file stored for this document")

    if doc.gcs_raw_uri.startswith("local://"):
        file_path = Path(doc.gcs_raw_uri.replace("local://", ""))
        if not file_path.exists():
            raise HTTPException(404, "File not found on disk")
        return FileResponse(file_path, media_type=doc.mime_type)

    # For GCS, download and return bytes
    file_bytes = download_file(doc.gcs_raw_uri)
    from fastapi.responses import Response
    return Response(content=file_bytes, media_type=doc.mime_type)


@router.post("/{doc_id}/extract")
async def trigger_extraction(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger AI extraction for a single document."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status not in ("uploaded", "failed"):
        raise HTTPException(400, f"Document is in '{doc.status}' state, cannot re-extract")

    doc.status = "extracting"
    await db.commit()

    try:
        # Download file
        file_bytes = download_file(doc.gcs_raw_uri)

        # Run AI extraction (or mock)
        extraction: ExtractionResult = await extract_from_document(file_bytes, doc.mime_type)

        # Persist results
        doc.extracted_json = extraction.model_dump()
        doc.overall_confidence = extraction.extraction_metadata.overall_confidence_score
        doc.low_confidence_fields = extraction.extraction_metadata.low_confidence_fields
        doc.is_form_readable = extraction.extraction_metadata.is_form_readable

        # Denormalize search fields
        ecvi = extraction.eCVI
        doc.cvi_number = ecvi.CviNumber
        if ecvi.IssueDate:
            from datetime import datetime
            try:
                doc.issue_date = datetime.strptime(ecvi.IssueDate, "%Y-%m-%d")
            except ValueError:
                pass
        if ecvi.Veterinarian:
            parts = [ecvi.Veterinarian.FirstName, ecvi.Veterinarian.LastName]
            doc.vet_name = " ".join(p for p in parts if p)

        doc.status = "review"

        db.add(AuditLog(
            document_id=doc.id,
            action="extracted",
            details={"confidence": doc.overall_confidence},
        ))

        await db.commit()
        await db.refresh(doc)

        # Update batch progress
        await _update_batch_progress(doc.batch_id, db)

        return {"status": "ok", "document_id": str(doc.id), "confidence": doc.overall_confidence}

    except Exception as e:
        logger.exception("Extraction failed for document %s", doc_id)
        doc.status = "failed"
        db.add(AuditLog(
            document_id=doc.id,
            action="extraction_failed",
            details={"error": str(e)},
        ))
        await db.commit()
        raise HTTPException(500, f"Extraction failed: {str(e)}")


@router.post("/{doc_id}/review")
async def submit_review(
    doc_id: str,
    submission: ReviewSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Submit a human review: approve with edits or mark unreadable."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.status not in ("review", "unreadable"):
        raise HTTPException(400, f"Document is in '{doc.status}' state, cannot review")

    if submission.action == "unreadable":
        doc.status = "unreadable"
        db.add(AuditLog(document_id=doc.id, action="marked_unreadable"))
        await db.commit()
        await _update_batch_progress(doc.batch_id, db)
        return {"status": "ok", "document_status": "unreadable"}

    elif submission.action == "approve":
        if not submission.edited_data:
            raise HTTPException(400, "edited_data is required for approval")

        ecvi_data: ECVIData = submission.edited_data
        doc.approved_json = ecvi_data.model_dump()

        # Update denormalized fields from approved data
        doc.cvi_number = ecvi_data.CviNumber
        if ecvi_data.IssueDate:
            from datetime import datetime
            try:
                doc.issue_date = datetime.strptime(ecvi_data.IssueDate, "%Y-%m-%d")
            except ValueError:
                pass
        if ecvi_data.Veterinarian:
            parts = [ecvi_data.Veterinarian.FirstName, ecvi_data.Veterinarian.LastName]
            doc.vet_name = " ".join(p for p in parts if p)

        # Generate XML
        xml_output = generate_ecvi_xml(ecvi_data)
        doc.xml_output = xml_output
        doc.status = "approved"

        # Archive XML
        try:
            xml_uri = upload_xml_to_archive(
                xml_output,
                ecvi_data.CviNumber or "unknown",
                str(doc.id),
            )
            doc.gcs_xml_uri = xml_uri
        except Exception as e:
            logger.warning("Failed to archive XML: %s", e)

        db.add(AuditLog(
            document_id=doc.id,
            action="approved",
            details={"cvi_number": ecvi_data.CviNumber},
        ))
        await db.commit()
        await _update_batch_progress(doc.batch_id, db)

        return {"status": "ok", "document_status": "approved", "xml": xml_output}

    else:
        raise HTTPException(400, f"Unknown action: {submission.action}")


async def _update_batch_progress(batch_id: str, db: AsyncSession):
    """Update the batch's processed document count."""
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        return

    doc_result = await db.execute(
        select(Document).where(Document.batch_id == batch_id)
    )
    docs = doc_result.scalars().all()
    done = sum(1 for d in docs if d.status in ("approved", "unreadable"))
    batch.processed_documents = done

    if done >= batch.total_documents:
        batch.status = "completed"
    elif any(d.status == "extracting" for d in docs):
        batch.status = "processing"

    await db.commit()
