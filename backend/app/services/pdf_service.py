from pathlib import Path
from typing import List

from pypdf import PdfReader

from app.chunking.semantic_chunker import SemanticChunker
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.page import Page

from app.utils.text_utils import (
    clean_text,
    detect_repeated_lines,
    remove_repeated_lines,
)


class PDFService:
    """
    Handles PDF extraction and semantic chunk creation.
    """

    def __init__(self):
        self.chunker = SemanticChunker()

    def _is_table_of_contents(
        self,
        text: str,
    ) -> bool:
        """
        Detects pages that are primarily table-of-contents content.

        The detection is generic and does not depend on a
        specific document title or subject.
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if len(lines) < 4:
            return False

        toc_indicators = 0

        for line in lines:

            # Lines containing dotted leaders and page numbers
            if (
                "..." in line
                and any(char.isdigit() for char in line)
            ):
                toc_indicators += 1
                continue

            # Lines that look like numbered chapter/section entries
            if line[:3].strip(".").isdigit():
                toc_indicators += 1
                continue

            # Common table-of-contents headings
            normalized = line.lower()

            if normalized in {
                "contents",
                "table of contents",
                "index",
            }:
                toc_indicators += 2

        # If a significant portion of the page looks like TOC
        return (
            toc_indicators >= 3
            and toc_indicators / len(lines) >= 0.30
        )

    def extract_document(
        self,
        pdf_path: Path,
    ) -> tuple[Document, List[Page]]:
        """
        Extract a document and its pages.

        Performs:
        - PDF text extraction
        - repeated header/footer detection
        - page-number cleanup
        - table-of-contents detection
        """

        reader = PdfReader(str(pdf_path))

        document = Document(
            filename=pdf_path.name,
            total_pages=len(reader.pages),
            status=DocumentStatus.PROCESSING,
        )

        # --------------------------------------------------
        # 1. RAW PAGE EXTRACTION
        # --------------------------------------------------

        raw_pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            text = page.extract_text() or ""

            if not text.strip():
                continue

            raw_pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

        # --------------------------------------------------
        # 2. DETECT REPEATED LINES
        # --------------------------------------------------

        repeated_lines = detect_repeated_lines(
            [
                page["text"]
                for page in raw_pages
            ]
        )

        print(
            f"Detected repeated PDF lines: "
            f"{len(repeated_lines)}"
        )

        # --------------------------------------------------
        # 3. CLEAN + FILTER PAGES
        # --------------------------------------------------

        pages: List[Page] = []

        toc_pages = 0

        for page_data in raw_pages:

            raw_text = page_data["text"]

            # Check TOC before removing repeated lines
            if self._is_table_of_contents(raw_text):

                toc_pages += 1

                print(
                    f"Skipping probable TOC page: "
                    f"{page_data['page_number']}"
                )

                continue

            cleaned_text = remove_repeated_lines(
                raw_text,
                repeated_lines,
            )

            cleaned_text = clean_text(
                cleaned_text
            )

            if not cleaned_text:
                continue

            pages.append(
                Page(
                    document_id=document.document_id,
                    filename=document.filename,
                    page_number=page_data["page_number"],
                    text=cleaned_text,
                )
            )

        print(
            f"TOC pages skipped: {toc_pages}"
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
        Header/footer cleanup
            ↓
        TOC filtering
            ↓
        Semantic chunks
        """

        document, pages = self.extract_document(
            pdf_path
        )

        chunks: List[Chunk] = []

        for page in pages:

            chunks.extend(
                self.chunker.chunk_page(page)
            )

        return document, chunks