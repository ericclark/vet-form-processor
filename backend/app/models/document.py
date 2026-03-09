import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False, unique=True)
    status = Column(String(32), nullable=False, default="pending")
    total_documents = Column(Float, default=0)
    processed_documents = Column(Float, default=0)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="batch", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=new_uuid)
    batch_id = Column(String(36), ForeignKey("batches.id"), nullable=False)
    original_filename = Column(String(512), nullable=False)
    gcs_raw_uri = Column(String(1024), nullable=True)
    gcs_archive_uri = Column(String(1024), nullable=True)
    mime_type = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="uploaded")

    # AI extraction results
    extracted_json = Column(JSON, nullable=True)
    overall_confidence = Column(Float, nullable=True)
    low_confidence_fields = Column(JSON, nullable=True)
    is_form_readable = Column(Boolean, nullable=True)

    # Approved / edited data
    approved_json = Column(JSON, nullable=True)

    # Final XML
    xml_output = Column(Text, nullable=True)
    gcs_xml_uri = Column(String(1024), nullable=True)

    # Key search fields (denormalized)
    cvi_number = Column(String(128), nullable=True, index=True)
    issue_date = Column(DateTime, nullable=True, index=True)
    vet_name = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batch = relationship("Batch", back_populates="documents")
    audit_logs = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    action = Column(String(64), nullable=False)
    user = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="audit_logs")
