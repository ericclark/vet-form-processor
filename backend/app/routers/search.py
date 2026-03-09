"""Search and repository endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String

from app.database import get_db
from app.models.document import Document
from app.schemas.api import DocumentSummary

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=List[DocumentSummary])
async def search_documents(
    cvi_number: Optional[str] = Query(None),
    vet_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    tag_number: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search approved/historical documents by various criteria."""
    query = select(Document)
    filters = []

    if cvi_number:
        filters.append(Document.cvi_number.ilike(f"%{cvi_number}%"))

    if vet_name:
        filters.append(Document.vet_name.ilike(f"%{vet_name}%"))

    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(Document.issue_date >= dt)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            filters.append(Document.issue_date <= dt)
        except ValueError:
            pass

    if tag_number:
        filters.append(
            cast(Document.extracted_json, String).ilike(f"%{tag_number}%")
        )

    if status:
        filters.append(Document.status == status)

    if filters:
        query = query.where(*filters)

    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()
