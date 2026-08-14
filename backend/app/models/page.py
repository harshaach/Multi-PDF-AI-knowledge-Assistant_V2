from uuid import UUID

from pydantic import BaseModel, Field


class Page(BaseModel):
    """
    Represents a single page extracted from a PDF document.
    """

    document_id: UUID = Field(
        ...,
        description="Unique identifier of the parent document."
    )

    filename: str = Field(
        ...,
        description="Original PDF filename."
    )

    page_number: int = Field(
        ...,
        ge=1,
        description="Page number in the document."
    )

    text: str = Field(
        ...,
        min_length=1,
        description="Extracted text from the page."
    )