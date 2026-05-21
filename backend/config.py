"""
Configuration management for the Enterprise Knowledge Base Q&A System.
Loads environment variables and provides validated settings.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
        self.KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")
        self.DATA_SOURCE_ID = os.getenv("DATA_SOURCE_ID", "")
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
        self.UPLOAD_PREFIX = os.getenv("UPLOAD_PREFIX", "uploads/")
        self.MODEL_ARN = os.getenv(
            "MODEL_ARN",
            f"arn:aws:bedrock:{self.AWS_REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
        )
        self.BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
        self.CORS_ORIGINS = os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")

    def validate(self):
        """Validate that all required settings are present."""
        errors = []

        if not self.KNOWLEDGE_BASE_ID or self.KNOWLEDGE_BASE_ID == "your-knowledge-base-id-here":
            errors.append(
                "KNOWLEDGE_BASE_ID is not set. "
                "Get it from AWS Console → Bedrock → Knowledge Bases and add it to backend/.env"
            )

        if not self.AWS_REGION:
            errors.append("AWS_REGION is not set.")

        if errors:
            print("\n Configuration Errors:")
            for err in errors:
                print(f"   • {err}")
            print("\n Copy backend/.env.example to backend/.env and fill in your values.\n")
            sys.exit(1)

        return True

    def get_model_display_name(self):
        """Extract a human-readable model name from the ARN."""
        if "claude-3-5-sonnet" in self.MODEL_ARN:
            return "Claude 3.5 Sonnet"
        elif "claude-3-sonnet" in self.MODEL_ARN:
            return "Claude 3 Sonnet"
        elif "claude-3-haiku" in self.MODEL_ARN:
            return "Claude 3 Haiku"
        elif "claude-3-opus" in self.MODEL_ARN:
            return "Claude 3 Opus"
        elif "titan" in self.MODEL_ARN.lower():
            return "Amazon Titan"
        elif "nova-pro" in self.MODEL_ARN:
            return "Amazon Nova Pro"
        elif "nova-lite" in self.MODEL_ARN:
            return "Amazon Nova Lite"
        elif "nova-micro" in self.MODEL_ARN:
            return "Amazon Nova Micro"
        else:
            # Return the model ID portion of the ARN
            return self.MODEL_ARN.split("/")[-1] if "/" in self.MODEL_ARN else self.MODEL_ARN


# Singleton settings instance
settings = Settings()
