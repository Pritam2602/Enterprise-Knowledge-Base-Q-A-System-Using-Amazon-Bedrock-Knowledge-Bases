"""
FastAPI application for the Enterprise Knowledge Base Q&A System.
Provides REST API endpoints for RAG queries, semantic search, and health checks.
"""

import time
import re
from pathlib import PurePath
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from config import settings
from bedrock_client import bedrock_client
from utils import (
    parse_retrieve_and_generate_response,
    parse_retrieve_response,
    sanitize_query,
)

# Validate configuration on startup
settings.validate()

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Knowledge Base Q&A API",
    description="RAG-powered Q&A system using Amazon Bedrock Knowledge Bases",
    version="1.0.0",
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Request body for RAG query endpoint."""
    question: str = Field(..., min_length=1, max_length=1000, description="The user's question")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of documents to retrieve")
    session_id: Optional[str] = Field(default=None, description="Session ID for multi-turn conversations")


class SearchRequest(BaseModel):
    """Request body for semantic search endpoint."""
    question: str = Field(..., min_length=1, max_length=1000, description="The search query")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of results to return")


class UploadUrlRequest(BaseModel):
    """Request body for creating a presigned S3 upload URL."""
    fileName: str = Field(..., min_length=1, max_length=255)
    fileType: str = Field(default="application/octet-stream", max_length=120)
    fileSize: int = Field(..., ge=1, le=50 * 1024 * 1024)


class UploadUrlResponse(BaseModel):
    """Response body for presigned upload URL creation."""
    uploadUrl: str
    s3Key: str
    expiresIn: int


class SyncKnowledgeBaseResponse(BaseModel):
    """Response body for starting a knowledge base ingestion job."""
    jobId: str
    status: str


class SyncStatusResponse(BaseModel):
    """Response body for ingestion job status checks."""
    jobId: str
    status: str
    statistics: Dict[str, Any] = Field(default_factory=dict)
    failureReasons: List[str] = Field(default_factory=list)


class CitationResponse(BaseModel):
    """A single citation/source reference."""
    documentName: str
    text: str
    s3Uri: str
    score: Optional[float]


class QueryResponse(BaseModel):
    """Response body for RAG query endpoint."""
    answer: str
    citations: List[CitationResponse]
    sessionId: str
    responseTime: float


class SearchResultResponse(BaseModel):
    """A single semantic search result."""
    documentName: str
    text: str
    s3Uri: str
    score: float


class SearchResponse(BaseModel):
    """Response body for semantic search endpoint."""
    results: List[SearchResultResponse]
    responseTime: float


class HealthResponse(BaseModel):
    """Response body for health check endpoint."""
    status: str
    region: str
    knowledgeBaseId: str
    model: Optional[str] = None
    error: Optional[str] = None


class ConfigResponse(BaseModel):
    """Response body for public config endpoint."""
    region: str
    model: str
    knowledgeBaseId: str
    dataSourceConfigured: bool
    uploadBucketConfigured: bool


ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt", ".html", ".htm", ".docx", ".csv", ".md"}
PRESIGNED_UPLOAD_TTL_SECONDS = 900


def _require_upload_config():
    """Ensure upload and ingestion settings are present before using admin endpoints."""
    missing = []
    if not settings.S3_BUCKET_NAME:
        missing.append("S3_BUCKET_NAME")
    if not settings.DATA_SOURCE_ID:
        missing.append("DATA_SOURCE_ID")

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing upload configuration: {', '.join(missing)}",
        )


def _build_s3_key(file_name: str) -> str:
    """Build a safe, unique S3 object key for a user-uploaded file."""
    original_name = PurePath(file_name).name
    extension = PurePath(original_name).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Allowed types: {allowed}",
        )

    stem = PurePath(original_name).stem
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "document"
    prefix = settings.UPLOAD_PREFIX.strip("/")

    if prefix:
        return f"{prefix}/{uuid4()}-{safe_stem}{extension}"
    return f"{uuid4()}-{safe_stem}{extension}"


# ─── API Endpoints ──────────────────────────────────────────────────────────

@app.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Full RAG query: retrieves relevant documents from the knowledge base
    and generates a grounded answer with citations.
    """
    # Sanitize the input
    clean_query = sanitize_query(request.question)
    if not clean_query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start_time = time.time()

    try:
        # Call Bedrock RetrieveAndGenerate
        raw_response = bedrock_client.retrieve_and_generate(
            query=clean_query,
            num_results=request.num_results,
            session_id=request.session_id,
        )

        # Parse the response
        parsed = parse_retrieve_and_generate_response(raw_response)
        elapsed = round(time.time() - start_time, 2)

        return QueryResponse(
            answer=parsed["answer"],
            citations=[CitationResponse(**c) for c in parsed["citations"]],
            sessionId=parsed["sessionId"],
            responseTime=elapsed,
        )

    except Exception as e:
        error_msg = str(e)

        # Provide user-friendly error messages
        if "AccessDeniedException" in error_msg:
            raise HTTPException(
                status_code=403,
                detail="Access denied to Bedrock. Check IAM permissions for bedrock:RetrieveAndGenerate.",
            )
        elif "ResourceNotFoundException" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge Base '{settings.KNOWLEDGE_BASE_ID}' not found. Verify the ID in your .env file.",
            )
        elif "ValidationException" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"Validation error: {error_msg}",
            )
        elif "ThrottlingException" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AWS API rate limit exceeded. Please try again in a few seconds.",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error querying knowledge base: {error_msg}",
            )


@app.post("/api/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    Semantic search only: retrieves relevant document chunks
    without generating an answer.
    """
    clean_query = sanitize_query(request.question)
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    start_time = time.time()

    try:
        raw_response = bedrock_client.retrieve_only(
            query=clean_query,
            num_results=request.num_results,
        )

        parsed = parse_retrieve_response(raw_response)
        elapsed = round(time.time() - start_time, 2)

        return SearchResponse(
            results=[SearchResultResponse(**r) for r in parsed],
            responseTime=elapsed,
        )

    except Exception as e:
        error_msg = str(e)
        if "AccessDeniedException" in error_msg:
            raise HTTPException(
                status_code=403,
                detail="Access denied to Bedrock. Check IAM permissions for bedrock:Retrieve.",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error searching knowledge base: {error_msg}",
            )


@app.post("/api/get-upload-url", response_model=UploadUrlResponse)
async def get_upload_url(request: UploadUrlRequest):
    """
    Create a presigned S3 PUT URL so the frontend can upload a document directly.
    """
    _require_upload_config()
    s3_key = _build_s3_key(request.fileName)

    try:
        upload_url = bedrock_client.create_upload_url(
            s3_key=s3_key,
            content_type=request.fileType,
            expires_in=PRESIGNED_UPLOAD_TTL_SECONDS,
        )
        return UploadUrlResponse(
            uploadUrl=upload_url,
            s3Key=s3_key,
            expiresIn=PRESIGNED_UPLOAD_TTL_SECONDS,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating upload URL: {str(e)}",
        )


@app.post("/api/sync-knowledge-base", response_model=SyncKnowledgeBaseResponse)
async def sync_knowledge_base():
    """
    Start a Bedrock Knowledge Base ingestion job for the configured data source.
    """
    _require_upload_config()

    try:
        response = bedrock_client.start_ingestion_job()
        ingestion_job = response.get("ingestionJob", {})
        return SyncKnowledgeBaseResponse(
            jobId=ingestion_job.get("ingestionJobId", ""),
            status=ingestion_job.get("status", "STARTING"),
        )
    except Exception as e:
        error_msg = str(e)
        if "ConflictException" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="An ingestion job is already running for this data source.",
            )
        if "AccessDeniedException" in error_msg:
            raise HTTPException(
                status_code=403,
                detail="Access denied to Bedrock ingestion. Check bedrock:StartIngestionJob permissions.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error starting knowledge base sync: {error_msg}",
        )


@app.get("/api/sync-status/{job_id}", response_model=SyncStatusResponse)
async def get_sync_status(job_id: str):
    """
    Get the latest status for a Bedrock Knowledge Base ingestion job.
    """
    _require_upload_config()

    try:
        response = bedrock_client.get_ingestion_job(job_id)
        ingestion_job = response.get("ingestionJob", {})
        return SyncStatusResponse(
            jobId=ingestion_job.get("ingestionJobId", job_id),
            status=ingestion_job.get("status", "UNKNOWN"),
            statistics=ingestion_job.get("statistics", {}),
            failureReasons=ingestion_job.get("failureReasons", []),
        )
    except Exception as e:
        error_msg = str(e)
        if "ResourceNotFoundException" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"Ingestion job '{job_id}' was not found.",
            )
        if "AccessDeniedException" in error_msg:
            raise HTTPException(
                status_code=403,
                detail="Access denied to Bedrock ingestion status. Check bedrock:GetIngestionJob permissions.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error checking sync status: {error_msg}",
        )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Check connectivity to the Bedrock Knowledge Base.
    Returns connection status and configuration details.
    """
    result = bedrock_client.check_connection()
    return HealthResponse(**result)


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """
    Return public (non-sensitive) configuration details.
    Used by the frontend to display model and region info.
    """
    return ConfigResponse(
        region=settings.AWS_REGION,
        model=settings.get_model_display_name(),
        knowledgeBaseId=settings.KNOWLEDGE_BASE_ID,
        dataSourceConfigured=bool(settings.DATA_SOURCE_ID),
        uploadBucketConfigured=bool(settings.S3_BUCKET_NAME),
    )


# ─── Startup Event ──────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Log startup confirmation."""
    print("\n" + "=" * 50)
    print("[KB] Enterprise Knowledge Base Q&A System")
    print("   Status: Running")
    print("=" * 50 + "\n")


# ─── Run with Uvicorn ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=True,
    )
