from typing import List
from app.config.settings import settings
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.chunk import Chunk


class EmbeddingService:
    """
    Handles embedding generation, FAISS indexing,
    and semantic search.
    """

    def __init__(
    self,
    model_name: str = settings.EMBEDDING_MODEL,
):
        self.model = SentenceTransformer(model_name)

        self.dimension = self.model.get_sentence_embedding_dimension()

        self.index = faiss.IndexFlatIP(self.dimension)

        self.chunks: List[Chunk] = []

    def add_chunks(self, chunks: List[Chunk]):

        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
        )

        faiss.normalize_L2(embeddings)

        self.index.add(embeddings.astype(np.float32))

        self.chunks.extend(chunks)

    def search(
    self,
    query: str,
    top_k: int = settings.DEFAULT_TOP_K,
    similarity_threshold: float = settings.SIMILARITY_THRESHOLD,
) -> List[tuple[Chunk, float]]:

        if self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
        )

        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(
            query_embedding.astype(np.float32),
            min(settings.MAX_TOP_K, self.index.ntotal),
        )

        results = []

        for idx, score in zip(indices[0], scores[0]):

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

        return results