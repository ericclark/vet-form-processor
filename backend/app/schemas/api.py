"""API request/response schemas."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.schemas.ecvi import ECVIData, ExtractionMetadata


class BatchResponse(BaseModel):
    id: str
    name: str
    status: str
    total_documents: int
    processed_documents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    overall_confidence: Optional[float] = None
    cvi_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    vet_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(BaseModel):
    id: str
    batch_id: str
    original_filename: str
    gcs_raw_uri: Optional[str] = None
    status: str
    extracted_json: Optional[dict] = None
    approved_json: Optional[dict] = None
    overall_confidence: Optional[float] = None
    low_confidence_fields: Optional[List[str]] = None
    is_form_readable: Optional[bool] = None
    cvi_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    vet_name: Optional[str] = None
    xml_output: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewSubmission(BaseModel):
    """Payload when a user approves or marks a document."""
    action: str  # "approve" or "unreadable"
    edited_data: Optional[ECVIData] = None


class SearchParams(BaseModel):
    cvi_number: Optional[str] = None
    vet_name: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tag_number: Optional[str] = None
    page: int = 1
    page_size: int = 25
