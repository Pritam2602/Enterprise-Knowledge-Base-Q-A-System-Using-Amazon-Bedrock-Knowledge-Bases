"""
Utility functions for the Enterprise Knowledge Base Q&A System.
Handles citation formatting, S3 URI parsing, and response structuring.
"""

import re
from urllib.parse import unquote


def extract_document_name(s3_uri: str) -> str:
    """
    Extract a human-readable document name from an S3 URI.

    Args:
        s3_uri: S3 URI like 's3://bucket-name/path/to/document.pdf'

    Returns:
        Clean document name like 'document.pdf'
    """
    if not s3_uri:
        return "Unknown Source"

    # Handle S3 URI format: s3://bucket/key
    if s3_uri.startswith("s3://"):
        path = s3_uri.split("s3://")[1]
        # Get the last part of the path (filename)
        filename = path.split("/")[-1] if "/" in path else path
    else:
        filename = s3_uri.split("/")[-1] if "/" in s3_uri else s3_uri

    # URL-decode the filename
    filename = unquote(filename)

    return filename if filename else "Unknown Source"


def format_citation(citation_data: dict) -> dict:
    """
    Format a raw Bedrock citation into a clean structure for the frontend.

    Args:
        citation_data: Raw citation object from Bedrock response

    Returns:
        Formatted citation dict with document name, text excerpt, and location
    """
    formatted = {
        "documentName": "Unknown Source",
        "text": "",
        "s3Uri": "",
        "score": None,
    }

    # Extract the retrieved reference
    references = citation_data.get("retrievedReferences", [])

    results = []
    for ref in references:
        entry = {
            "documentName": "Unknown Source",
            "text": "",
            "s3Uri": "",
            "score": None,
        }

        # Extract content text
        content = ref.get("content", {})
        entry["text"] = content.get("text", "")

        # Extract S3 location
        location = ref.get("location", {})
        s3_location = location.get("s3Location", {})
        s3_uri = s3_location.get("uri", "")
        entry["s3Uri"] = s3_uri
        entry["documentName"] = extract_document_name(s3_uri)

        # Extract relevance score if available
        metadata = ref.get("metadata", {})
        if "score" in metadata:
            entry["score"] = round(float(metadata["score"]), 3)

        results.append(entry)

    return results


def parse_retrieve_and_generate_response(response: dict) -> dict:
    """
    Parse the full Bedrock RetrieveAndGenerate response into a clean format.

    Args:
        response: Raw boto3 response from retrieve_and_generate

    Returns:
        Structured dict with answer text and formatted citations
    """
    result = {
        "answer": "",
        "citations": [],
        "sessionId": "",
    }

    # Extract the generated output text
    output = response.get("output", {})
    result["answer"] = output.get("text", "No answer generated.")

    # Extract session ID for multi-turn conversations
    result["sessionId"] = response.get("sessionId", "")

    # Parse citations
    raw_citations = response.get("citations", [])
    for citation in raw_citations:
        formatted_refs = format_citation(citation)
        result["citations"].extend(formatted_refs)

    # Remove duplicate citations and filter out unknown sources
    seen = set()
    unique_citations = []
    for c in result["citations"]:
        # Skip citations with no real source
        if c["documentName"] == "Unknown Source" or not c["text"]:
            continue
        key = (c["documentName"], c["text"][:100])
        if key not in seen:
            seen.add(key)
            unique_citations.append(c)
    result["citations"] = unique_citations

    return result


def parse_retrieve_response(response: dict) -> list:
    """
    Parse the Bedrock Retrieve response into a list of search results.

    Args:
        response: Raw boto3 response from retrieve

    Returns:
        List of dicts with document name, text, score, and S3 URI
    """
    results = []

    retrieval_results = response.get("retrievalResults", [])
    for item in retrieval_results:
        content = item.get("content", {})
        location = item.get("location", {})
        s3_location = location.get("s3Location", {})
        s3_uri = s3_location.get("uri", "")

        result = {
            "documentName": extract_document_name(s3_uri),
            "text": content.get("text", ""),
            "s3Uri": s3_uri,
            "score": round(float(item.get("score", 0)), 3),
        }
        results.append(result)

    return results


def sanitize_query(query: str) -> str:
    """
    Clean and validate user query input.

    Args:
        query: Raw user input

    Returns:
        Sanitized query string
    """
    if not query:
        return ""

    # Strip whitespace
    query = query.strip()

    # Remove excessive whitespace
    query = re.sub(r"\s+", " ", query)

    # Limit length to prevent abuse
    max_length = 1000
    if len(query) > max_length:
        query = query[:max_length]

    return query
