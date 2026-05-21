"""
Amazon Bedrock Knowledge Base client for the Enterprise Q&A System.
Wraps boto3 calls to Bedrock's RetrieveAndGenerate and Retrieve APIs.
"""

import time
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from config import settings


class BedrockKBClient:
    """Client for interacting with Amazon Bedrock Knowledge Bases."""

    def __init__(self):
        """Initialize the Bedrock Agent Runtime client."""
        self.region = settings.AWS_REGION
        self.knowledge_base_id = settings.KNOWLEDGE_BASE_ID
        self.model_arn = settings.MODEL_ARN

        # Initialize boto3 clients for runtime Q&A, ingestion, and uploads.
        self.client = boto3.client(
            service_name="bedrock-agent-runtime",
            region_name=self.region,
        )
        self.agent_client = boto3.client(
            service_name="bedrock-agent",
            region_name=self.region,
        )
        self.s3_client = boto3.client(
            service_name="s3",
            region_name=self.region,
        )

    def create_upload_url(
        self,
        s3_key: str,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        """
        Create a presigned S3 PUT URL for direct browser uploads.

        Args:
            s3_key: Destination object key in the configured S3 bucket
            content_type: MIME type the browser will send with the PUT request
            expires_in: URL lifetime in seconds

        Returns:
            Presigned PUT URL
        """
        return self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    def start_ingestion_job(self) -> dict:
        """
        Start a Bedrock Knowledge Base ingestion job for the configured data source.

        Returns:
            Raw boto3 response from Bedrock Agent
        """
        return self._call_with_retry(
            self.agent_client.start_ingestion_job,
            knowledgeBaseId=self.knowledge_base_id,
            dataSourceId=settings.DATA_SOURCE_ID,
        )

    def get_ingestion_job(self, job_id: str) -> dict:
        """
        Fetch the latest status for a Bedrock Knowledge Base ingestion job.

        Args:
            job_id: Ingestion job ID returned by start_ingestion_job

        Returns:
            Raw boto3 response from Bedrock Agent
        """
        return self._call_with_retry(
            self.agent_client.get_ingestion_job,
            knowledgeBaseId=self.knowledge_base_id,
            dataSourceId=settings.DATA_SOURCE_ID,
            ingestionJobId=job_id,
        )

    def retrieve_and_generate(
        self,
        query: str,
        num_results: int = 5,
        session_id: str = None,
    ) -> dict:
        """
        Perform full RAG: retrieve relevant documents and generate an answer.

        Args:
            query: The user's natural language question
            num_results: Number of document chunks to retrieve (1-10)
            session_id: Optional session ID for multi-turn conversations

        Returns:
            Raw boto3 response from Bedrock

        Raises:
            ClientError: AWS API errors
            BotoCoreError: Low-level AWS SDK errors
        """
        # Build the request parameters
        params = {
            "input": {"text": query},
            "retrieveAndGenerateConfiguration": {
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": self.knowledge_base_id,
                    "modelArn": self.model_arn,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": num_results,
                        }
                    },
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": (
                                "You are a strict enterprise knowledge base assistant. "
                                "You must ONLY answer based on the retrieved information below. "
                                "Do NOT use any prior knowledge or general information. "
                                "If the retrieved information does not contain relevant details "
                                "to answer the question, respond ONLY with: "
                                "'I don't have information about this topic in the knowledge base. "
                                "Please ask a question related to the documents available in the system.'\n\n"
                                "Retrieved information:\n$search_results$\n\n"
                                "User question: $query$\n\n"
                                "Answer (based strictly on retrieved information only):"
                            )
                        }
                    },
                },
            },
        }

        # Include session ID for multi-turn conversations
        if session_id:
            params["sessionId"] = session_id

        # Make the API call with retry logic
        response = self._call_with_retry(
            self.client.retrieve_and_generate,
            **params,
        )

        return response

    def retrieve_only(
        self,
        query: str,
        num_results: int = 5,
    ) -> dict:
        """
        Perform semantic search only — return relevant document chunks
        without LLM generation.

        Args:
            query: The user's natural language question
            num_results: Number of document chunks to retrieve (1-10)

        Returns:
            Raw boto3 response with retrieval results

        Raises:
            ClientError: AWS API errors
        """
        params = {
            "knowledgeBaseId": self.knowledge_base_id,
            "retrievalQuery": {"text": query},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": num_results,
                }
            },
        }

        response = self._call_with_retry(
            self.client.retrieve,
            **params,
        )

        return response

    def _call_with_retry(self, func, max_retries: int = 3, **kwargs) -> dict:
        """
        Call an AWS API function with exponential backoff retry logic.

        Handles throttling (429) and transient server errors (5xx).

        Args:
            func: The boto3 client method to call
            max_retries: Maximum number of retry attempts
            **kwargs: Arguments to pass to the function

        Returns:
            API response dict

        Raises:
            ClientError: If all retries are exhausted
        """
        for attempt in range(max_retries):
            try:
                response = func(**kwargs)
                return response

            except ClientError as e:
                error_code = e.response["Error"]["Code"]

                # Retry on throttling or server errors
                if error_code in (
                    "ThrottlingException",
                    "ServiceUnavailableException",
                    "InternalServerException",
                ) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 0.5  # Exponential backoff
                    print(
                        f"[WARN] AWS API throttled (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                # Don't retry on access denied, validation errors, etc.
                raise

            except BotoCoreError as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 0.5
                    print(f"[WARN] AWS SDK error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                raise

    def check_connection(self) -> dict:
        """
        Verify connectivity to the Bedrock Knowledge Base.

        Returns:
            Dict with status and details
        """
        try:
            # Attempt a minimal retrieve call to verify access
            self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": "test"},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": 1,
                    }
                },
            )
            return {
                "status": "connected",
                "region": self.region,
                "knowledgeBaseId": self.knowledge_base_id,
                "model": settings.get_model_display_name(),
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return {
                "status": "error",
                "error": f"{error_code}: {error_message}",
                "region": self.region,
                "knowledgeBaseId": self.knowledge_base_id,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "region": self.region,
                "knowledgeBaseId": self.knowledge_base_id,
            }


# Singleton client instance
bedrock_client = BedrockKBClient()
