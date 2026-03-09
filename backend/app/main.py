"""FastAPI application entry point for BOAH AutoExtract Agent."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import upload, documents, search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (SQLite local dev)
    logger.info("Creating database tables...")
    # Import models so they're registered
    from app.models.document import Batch, Document, AuditLog  # noqa: F401
    await create_tables()
    logger.info("Database ready. Storage mode: %s, Extraction mode: %s",
                "local" if settings.use_local_storage else "GCS",
                "mock" if settings.use_mock_extraction else "Vertex AI")
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AutoExtract Agent for Indiana Board of Animal Health - eCVI form processing",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "storage": "local" if settings.use_local_storage else "GCS",
        "extraction": "mock" if settings.use_mock_extraction else "Vertex AI",
    }
