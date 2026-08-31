from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config.settings import settings
from app.models.chunk import Chunk


class EmbeddingService:
    """
    Handles embedding generation, FAISS indexing,
    and semantic search.

    Each workspace owns one EmbeddingService,
    so documents remain isolated per chat/workspace.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL,
    ):
        self.model = SentenceTransformer(model_name)

        self.dimension = (
            self.model.get_sentence_embedding_dimension()
        )

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

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
        )

        faiss.normalize_L2(
            embeddings
        )

        self.index.add(
            embeddings.astype(np.float32)
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

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
        )

        faiss.normalize_L2(
            embeddings
        )

        self.index.add(
            embeddings.astype(np.float32)
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

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
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
            query_embedding.astype(np.float32),
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