"""
FastAPI application for the Enterprise Knowledge Base Q&A System.
Provides REST API endpoints for RAG queries, semantic search, and health checks.
"""

import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

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
    )


# ─── Startup Event ──────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Log configuration on startup."""
    print("\n" + "=" * 60)
    print("🧠 Enterprise Knowledge Base Q&A System")
    print("=" * 60)
    print(f"   Region:          {settings.AWS_REGION}")
    print(f"   Knowledge Base:  {settings.KNOWLEDGE_BASE_ID}")
    print(f"   Model:           {settings.get_model_display_name()}")
    print(f"   CORS Origins:    {', '.join(settings.CORS_ORIGINS)}")
    print("=" * 60 + "\n")


# ─── Run with Uvicorn ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=True,
    )
