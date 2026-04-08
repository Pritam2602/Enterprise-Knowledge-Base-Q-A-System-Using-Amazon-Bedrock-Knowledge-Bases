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
