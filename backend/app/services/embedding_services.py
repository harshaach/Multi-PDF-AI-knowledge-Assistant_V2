from typing import List

import faiss
import numpy as np
from google import genai
from google.genai import types

from app.config.settings import settings
from app.models.chunk import Chunk

# Loaded once, shared by every workspace — a lightweight API client, not a local model.
_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_EMBEDDING_MODEL = "gemini-embedding-001"
_EMBEDDING_DIM = 768  # reduced output dimensionality (keeps FAISS index small)


def _embed_texts(texts: List[str], task_type: str) -> np.ndarray:
    """
    Calls Gemini's embedding API for a batch of texts.

    task_type: 'RETRIEVAL_DOCUMENT' for chunks being indexed,
               'RETRIEVAL_QUERY' for search queries.
    """
    result = _client.models.embed_content(
        model=_EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=_EMBEDDING_DIM,
        ),
    )

    vectors = [e.values for e in result.embeddings]

    return np.array(vectors, dtype=np.float32)


class EmbeddingService:
    """
    Handles embedding generation (via Gemini API), FAISS indexing,
    and semantic search.

    Each workspace owns one EmbeddingService, so documents remain
    isolated per chat/workspace. The embedding client itself is a
    shared, lightweight API client — not a local model — so this
    is cheap to create per workspace.
    """

    def __init__(self):
        self.dimension = _EMBEDDING_DIM

        self.index = faiss.IndexFlatIP(
            self.dimension
        )

        self.chunks: List[Chunk] = []

    # =========================================================
    # ADD CHUNKS
    # =========================================================

    def add_chunks(
        self,
        chunks: List[Chunk],
    ):
        """
        Add new document chunks to the FAISS index.

        Existing documents are not duplicated.
        """

        if not chunks:
            return

        self._remove_document(
            chunks[0].document_id
        )

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = _embed_texts(
            texts,
            task_type="RETRIEVAL_DOCUMENT",
        )

        faiss.normalize_L2(
            embeddings
        )

        self.index.add(
            embeddings
        )

        self.chunks.extend(chunks)

    # =========================================================
    # REMOVE DOCUMENT
    # =========================================================

    def _remove_document(
        self,
        document_id,
    ):
        """
        Remove an existing document from the
        in-memory chunk collection and rebuild FAISS.
        """

        existing_chunks = [
            chunk
            for chunk in self.chunks
            if chunk.document_id != document_id
        ]

        # Nothing to remove
        if len(existing_chunks) == len(self.chunks):
            return

        self.chunks = existing_chunks

        self._rebuild_index()

    # =========================================================
    # REBUILD INDEX
    # =========================================================

    def _rebuild_index(self):
        """
        Rebuild FAISS from the current chunk collection.
        """

        self.index = faiss.IndexFlatIP(
            self.dimension
        )

        if not self.chunks:
            return

        texts = [
            chunk.text
            for chunk in self.chunks
        ]

        embeddings = _embed_texts(
            texts,
            task_type="RETRIEVAL_DOCUMENT",
        )

        faiss.normalize_L2(
            embeddings
        )

        self.index.add(
            embeddings
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        top_k: int = settings.DEFAULT_TOP_K,
        similarity_threshold: float = (
            settings.SIMILARITY_THRESHOLD
        ),
    ) -> List[tuple[Chunk, float]]:

        if self.index.ntotal == 0:
            return []

        # -----------------------------------------------------
        # Query embedding
        # -----------------------------------------------------

        embedding_start = __import__(
            "time"
        ).perf_counter()

        query_embedding = _embed_texts(
            [query],
            task_type="RETRIEVAL_QUERY",
        )

        faiss.normalize_L2(
            query_embedding
        )

        embedding_time = (
            __import__("time").perf_counter()
            - embedding_start
        )

        print(
            f"Query embedding time: "
            f"{embedding_time:.4f} sec"
        )

        # -----------------------------------------------------
        # FAISS search
        # -----------------------------------------------------

        faiss_start = __import__(
            "time"
        ).perf_counter()

        search_k = min(
            settings.MAX_TOP_K,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            query_embedding,
            search_k,
        )

        faiss_time = (
            __import__("time").perf_counter()
            - faiss_start
        )

        print(
            f"FAISS search time: "
            f"{faiss_time:.6f} sec"
        )

        # -----------------------------------------------------
        # Threshold filtering
        # -----------------------------------------------------

        results = []

        for idx, score in zip(
            indices[0],
            scores[0],
        ):

            if idx == -1:
                continue

            if score < similarity_threshold:
                continue

            results.append(
                (
                    self.chunks[idx],
                    float(score),
                )
            )

            if len(results) >= top_k:
                break

        print(
            f"Similarity threshold: "
            f"{similarity_threshold:.2f}"
        )

        print(
            f"Chunks above threshold: "
            f"{len(results)}"
        )

        return results
