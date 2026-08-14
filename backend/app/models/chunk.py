from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    Represents a semantic chunk extracted from a PDF page.
    """

    chunk_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the chunk."
    )

    document_id: UUID = Field(
        ...,
        description="Parent document identifier."
    )

    filename: str = Field(
        ...,
        description="Original PDF filename."
    )

    page_number: int = Field(
        ...,
        ge=1,
        description="Page number where this chunk belongs."
    )

    chunk_index: int = Field(
        ...,
        ge=0,
        description="Chunk index within the document."
    )

    text: str = Field(
        ...,
        min_length=1,
        description="Semantic chunk text."
    )

    character_count: int = Field(
        ...,
        ge=1,
        description="Number of characters in the chunk."
    )

    sentence_count: int = Field(
        ...,
        ge=1,
        description="Number of sentences in the chunk."
    )