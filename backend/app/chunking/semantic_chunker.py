from typing import List
from app.chunking.base_chunker import BaseChunker
from app.models.chunk import Chunk
from app.models.page import Page
from app.utils.text_utils import (
    clean_text,
    split_into_paragraphs,
    split_into_sentences,
)


class SemanticChunker(BaseChunker):
    """
    Creates semantic chunks from PDF pages.
    """

    def __init__(
        self,
        target_chunk_size: int = 1500,
        overlap_sentences: int = 2,
    ):
        self.target_chunk_size = target_chunk_size
        self.overlap_sentences = overlap_sentences

    def chunk_page(self, page: Page) -> List[Chunk]:
        """
        Converts one Page into a list of semantic Chunk objects.
        """

        text = clean_text(page.text)

        paragraphs = split_into_paragraphs(text)

        chunks: List[Chunk] = []

        chunk_index = 0

        current_sentences = []

        current_size = 0

        for paragraph in paragraphs:

            sentences = split_into_sentences(paragraph)

            for sentence in sentences:

                sentence_length = len(sentence)

                if (
                    current_sentences
                    and current_size + sentence_length > self.target_chunk_size
                ):

                    chunk_text = " ".join(current_sentences)

                    chunks.append(
                        self._build_chunk(
                            page,
                            chunk_index,
                            chunk_text,
                            len(current_sentences),
                        )
                    )

                    overlap = current_sentences[-self.overlap_sentences :]

                    current_sentences = overlap.copy()

                    current_size = sum(len(s) for s in current_sentences)

                    chunk_index += 1

                current_sentences.append(sentence)

                current_size += sentence_length

        if current_sentences:

            chunk_text = " ".join(current_sentences)

            chunks.append(
                self._build_chunk(
                    page,
                    chunk_index,
                    chunk_text,
                    len(current_sentences),
                )
            )

        return chunks

    def _build_chunk(
        self,
        page: Page,
        chunk_index: int,
        text: str,
        sentence_count: int,
    ) -> Chunk:

        return Chunk(
            document_id=page.document_id,
            filename=page.filename,
            page_number=page.page_number,
            chunk_index=chunk_index,
            text=text,
            character_count=len(text),
            sentence_count=sentence_count,
        )