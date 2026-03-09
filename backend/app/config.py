
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "BOAH AutoExtract Agent"
    debug: bool = False

    # Local vs GCP mode
    use_local_storage: bool = True
    use_mock_extraction: bool = True
    local_storage_path: str = "./local_storage"

    # Database - defaults to local SQLite
    database_url: str = "sqlite+aiosqlite:///./boah.db"
    database_url_sync: str = "sqlite:///./boah.db"

    # GCS Buckets (only used when use_local_storage=False)
    gcs_staging_bucket: str = "boah-staging"
    gcs_raw_forms_bucket: str = "boah-raw-forms"
    gcs_archive_bucket: str = "boah-archive"

    # Vertex AI (only used when use_mock_extraction=False)
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-pro"

    # Upload limits
    max_upload_size_mb: int = 50
    allowed_mime_types: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/zip",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def storage_root(self) -> Path:
        p = Path(self.local_storage_path)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
