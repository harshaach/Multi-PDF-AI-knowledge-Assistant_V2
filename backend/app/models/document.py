from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """
    Represents the current processing state of a document.
    """

    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Represents a single uploaded PDF document.
    """

    document_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the document."
    )

    filename: str = Field(
        ...,
        description="Original name of the uploaded PDF."
    )

    upload_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the document was uploaded."
    )

    total_pages: int = Field(
        ...,
        ge=1,
        description="Total number of pages in the document."
    )

    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADING,
        description="Current processing status of the document."
    )