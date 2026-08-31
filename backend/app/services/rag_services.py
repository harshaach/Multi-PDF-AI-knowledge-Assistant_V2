from google import genai
import time

from app.config.settings import settings
from app.services.embedding_services import EmbeddingService


class RAGService:
    """
    Retrieval-first RAG Service.

    Pipeline:

    Question
        ↓
    FAISS Retrieval
        ↓
    Similarity Threshold (0.45)
        ↓
    Relevant?
      ├── YES → Document RAG + Gemini
      └── NO  → General Gemini

    This removes the Gemini query-router call from
    the normal query path, reducing latency and API usage.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        api_key: str,
    ):
        self.embedding_service = embedding_service
        self.client = genai.Client(api_key=api_key)

    # --------------------------------------------------
    # Main RAG Pipeline
    # --------------------------------------------------

    def ask(
        self,
        question: str,
        top_k: int = settings.DEFAULT_TOP_K,
    ):
        total_start = time.perf_counter()

        print("\n" + "=" * 60)
        print("RAG DIAGNOSTIC")
        print("=" * 60)
        print(f"Question: {question}")

        # --------------------------------------------------
        # 1. RETRIEVAL
        # --------------------------------------------------

        retrieval_start = time.perf_counter()

        retrieved = self.embedding_service.search(
            question,
            top_k,
        )

        retrieval_time = (
            time.perf_counter() - retrieval_start
        )

        print(
            f"Retrieval time: "
            f"{retrieval_time:.4f} sec"
        )

        print(
            f"Retrieved chunks: "
            f"{len(retrieved)}"
        )

        # --------------------------------------------------
        # 2. NO RELEVANT DOCUMENT CONTEXT
        # --------------------------------------------------

        if not retrieved:

            print(
                "NO CHUNKS PASSED THE SIMILARITY THRESHOLD"
            )

            llm_start = time.perf_counter()

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=question,
            )

            llm_time = (
                time.perf_counter() - llm_start
            )

            total_time = (
                time.perf_counter() - total_start
            )

            print(
                f"LLM generation time: "
                f"{llm_time:.4f} sec"
            )

            print(
                f"Total query time: "
                f"{total_time:.4f} sec"
            )

            print("=" * 60)

            return {
                "answer": response.text,
                "sources": [],
            }

        # --------------------------------------------------
        # 3. RETRIEVAL DETAILS
        # --------------------------------------------------

        print("\nRetrieved chunks:")

        for i, (chunk, score) in enumerate(
            retrieved,
            start=1,
        ):
            print(
                f"{i}. "
                f"file={chunk.filename}, "
                f"page={chunk.page_number}, "
                f"chunk={chunk.chunk_index}, "
                f"score={score:.4f}"
            )

        # --------------------------------------------------
        # 4. CONTEXT CONSTRUCTION
        # --------------------------------------------------

        context_start = time.perf_counter()

        context_parts = []
        sources = set()

        for chunk, score in retrieved:

            context_parts.append(
                f"[Source: {chunk.filename}]\n"
                f"Page: {chunk.page_number}\n"
                f"Similarity: {score:.3f}\n"
                f"{chunk.text}"
            )

            sources.add(
                f"{chunk.filename} - Page {chunk.page_number}"
            )

        context = "\n\n".join(context_parts)

        context_time = (
            time.perf_counter() - context_start
        )

        print(
            f"Context construction time: "
            f"{context_time:.4f} sec"
        )

        print(
            f"Context characters: "
            f"{len(context)}"
        )

        # --------------------------------------------------
        # 5. DOCUMENT RAG PROMPT
        # --------------------------------------------------

        prompt = f"""
You are an AI Knowledge Assistant.

Answer the user's question using ONLY
the retrieved document context below.

Rules:

- Use only the provided document context.
- Do not use outside knowledge.
- Do not invent information.
- If the answer cannot be determined from
  the provided context, say:

"I couldn't find sufficient information
in the uploaded documents."

- Give a clear and concise answer.

Document Context:

{context}

Question:

{question}

Answer:
"""

        # --------------------------------------------------
        # 6. LLM GENERATION
        # --------------------------------------------------

        llm_start = time.perf_counter()

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        llm_time = (
            time.perf_counter() - llm_start
        )

        total_time = (
            time.perf_counter() - total_start
        )

        # --------------------------------------------------
        # 7. FINAL DIAGNOSTICS
        # --------------------------------------------------

        print(
            f"LLM generation time: "
            f"{llm_time:.4f} sec"
        )

        print(
            f"Total query time: "
            f"{total_time:.4f} sec"
        )

        print(
            f"Sources returned: "
            f"{len(sources)}"
        )

        print("=" * 60)

        return {
            "answer": response.text,
            "sources": list(sources),
        }