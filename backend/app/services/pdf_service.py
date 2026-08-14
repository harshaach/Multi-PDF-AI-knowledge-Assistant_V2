from pathlib import Path
from typing import List

from pypdf import PdfReader

from app.chunking.semantic_chunker import SemanticChunker
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.page import Page


class PDFService:
    """
    Handles PDF extraction and semantic chunk creation.
    """

    def __init__(self):
        self.chunker = SemanticChunker()

    def extract_document(self, pdf_path: Path) -> tuple[Document, List[Page]]:
        """
        Extract a document and its pages.
        """

        reader = PdfReader(str(pdf_path))

        document = Document(
            filename=pdf_path.name,
            total_pages=len(reader.pages),
            status=DocumentStatus.PROCESSING,
        )

        pages: List[Page] = []

        for page_number, page in enumerate(reader.pages, start=1):

            text = (page.extract_text() or "").strip()

            if not text:
                continue

            pages.append(
                Page(
                    document_id=document.document_id,
                    filename=document.filename,
                    page_number=page_number,
                    text=text,
                )
            )

        document.status = DocumentStatus.INDEXED

        return document, pages

    def extract_chunks(
        self,
        pdf_path: Path,
    ) -> tuple[Document, List[Chunk]]:

        """
        Complete ingestion pipeline.

        PDF
            ↓
        Document
            ↓
        Pages
            ↓
        Semantic Chunks
        """

        document, pages = self.extract_document(pdf_path)

        chunks: List[Chunk] = []

        for page in pages:
            chunks.extend(
                self.chunker.chunk_page(page)
            )

        return document, chunks