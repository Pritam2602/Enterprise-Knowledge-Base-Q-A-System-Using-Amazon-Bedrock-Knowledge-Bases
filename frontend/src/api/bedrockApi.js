/**
 * API client for the Enterprise Knowledge Base Q&A backend.
 * Handles all communication with the FastAPI server.
 */

const API_BASE = '/api';

/**
 * Send a RAG query to the knowledge base.
 * Returns an answer with citations.
 */
export async function sendQuery(question, numResults = 5, sessionId = null) {
  const body = {
    question,
    num_results: numResults,
  };

  if (sessionId) {
    body.session_id = sessionId;
  }

  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Perform semantic search only (no LLM generation).
 * Returns matching document chunks with scores.
 */
export async function searchDocuments(question, numResults = 5) {
  const response = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, num_results: numResults }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Request a presigned S3 PUT URL for a document upload.
 */
export async function getUploadUrl(file) {
  const response = await fetch(`${API_BASE}/get-upload-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fileName: file.name,
      fileType: file.type || 'application/octet-stream',
      fileSize: file.size,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Start ingestion for the configured Bedrock Knowledge Base data source.
 */
export async function syncKnowledgeBase() {
  const response = await fetch(`${API_BASE}/sync-knowledge-base`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Check ingestion job status.
 */
export async function getSyncStatus(jobId) {
  const response = await fetch(`${API_BASE}/sync-status/${encodeURIComponent(jobId)}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health and Bedrock connectivity.
 */
export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get public configuration (region, model name, etc.)
 */
export async function getConfig() {
  const response = await fetch(`${API_BASE}/config`);

  if (!response.ok) {
    throw new Error(`Config fetch failed: HTTP ${response.status}`);
  }

  return response.json();
}
