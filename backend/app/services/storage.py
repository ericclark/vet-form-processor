"""File storage service - local filesystem or GCS."""


import logging
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _local_path(subdir: str, *parts: str) -> Path:
    p = settings.storage_root / subdir / "/".join(parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def upload_to_raw(file_bytes: bytes, filename: str, mime_type: str) -> str:
    """Store a file. Returns a URI (local path or gs://)."""
    blob_name = f"{uuid.uuid4()}/{filename}"

    if settings.use_local_storage:
        path = _local_path("raw-forms", blob_name)
        path.write_bytes(file_bytes)
        uri = f"local://{path}"
        logger.info("Stored locally: %s", uri)
        return uri

    from google.cloud import storage as gcs
    client = gcs.Client(project=settings.gcp_project_id)
    bucket = client.bucket(settings.gcs_raw_forms_bucket)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type=mime_type)
    uri = f"gs://{settings.gcs_raw_forms_bucket}/{blob_name}"
    logger.info("Uploaded to %s", uri)
    return uri


def upload_xml_to_archive(xml_content: str, cvi_number: str, doc_id: str) -> str:
    """Store generated XML. Returns a URI."""
    blob_name = f"xml/{doc_id}/{cvi_number}.xml"

    if settings.use_local_storage:
        path = _local_path("archive", blob_name)
        path.write_text(xml_content, encoding="utf-8")
        uri = f"local://{path}"
        logger.info("Archived XML locally: %s", uri)
        return uri

    from google.cloud import storage as gcs
    client = gcs.Client(project=settings.gcp_project_id)
    bucket = client.bucket(settings.gcs_archive_bucket)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(xml_content, content_type="application/xml")
    uri = f"gs://{settings.gcs_archive_bucket}/{blob_name}"
    logger.info("Archived XML to %s", uri)
    return uri


def download_file(uri: str) -> bytes:
    """Download a file by its URI."""
    if uri.startswith("local://"):
        path = Path(uri.replace("local://", ""))
        return path.read_bytes()

    from google.cloud import storage as gcs
    client = gcs.Client(project=settings.gcp_project_id)
    parts = uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(parts[0])
    blob = bucket.blob(parts[1])
    return blob.download_as_bytes()


def get_file_url(uri: str) -> str:
    """Get a servable URL for the file. For local, returns an API path."""
    if uri.startswith("local://"):
        # Will be served via a /api/files/ endpoint
        path = uri.replace("local://", "")
        return f"/api/files/{path}"
    # For GCS, would generate a signed URL
    return uri
