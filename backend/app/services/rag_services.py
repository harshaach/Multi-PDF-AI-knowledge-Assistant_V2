from google import genai

from app.config.settings import settings
from app.services.embedding_services import EmbeddingService


class RAGService:
    """
    Intelligent RAG Service

    Supports:
    - DOCUMENT queries
    - GENERAL queries
    - HYBRID queries
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        api_key: str,
    ):
        self.embedding_service = embedding_service
        self.client = genai.Client(api_key=api_key)

    # --------------------------------------------------
    # Query Router
    # --------------------------------------------------

    def route_query(self, question: str) -> str:
        """
        Decide whether the query should use:

        DOCUMENT
        GENERAL
        HYBRID
        """

        router_prompt = f"""
You are an intelligent query router.

Your job is to classify the user's question into ONLY ONE category.

DOCUMENT
- The answer should come ONLY from uploaded documents.

GENERAL
- The answer is general knowledge.
- Uploaded documents are NOT required.

HYBRID
- The answer requires BOTH uploaded documents and general knowledge.

Reply with ONLY one word.

DOCUMENT
GENERAL
HYBRID

Question:
{question}
"""

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=router_prompt,
        )

        route = response.text.strip().upper()

        if route not in ["DOCUMENT", "GENERAL", "HYBRID"]:
            route = "DOCUMENT"

        return route

    # --------------------------------------------------
    # Main RAG Pipeline
    # --------------------------------------------------

    def ask(
        self,
        question: str,
        top_k: int = settings.DEFAULT_TOP_K,
    ):
        route = self.route_query(question)
        print(f"Route: {route}")

        print(f"\nQuery Route: {route}")

        # ==========================================
        # GENERAL KNOWLEDGE
        # ==========================================

        if route == "GENERAL":

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=question,
            )

            return {
                "answer": response.text,
                "sources": [],
            }

        # ==========================================
        # DOCUMENT / HYBRID
        # ==========================================

        retrieved = self.embedding_service.search(
            question,
            top_k,
            
        )
        print(f"Retrieved Chunks: {len(retrieved)}")

        if not retrieved:

            if route == "DOCUMENT":

                return {
                    "answer": "I couldn't find sufficient information in the uploaded documents.",
                    "sources": [],
                }

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=question,
            )

            return {
                "answer": response.text,
                "sources": [],
            }

        context = ""

        sources = set()

        for chunk, score in retrieved:

            context += (
                f"\n\n"
                f"[Source: {chunk.filename}]"
                f"\nSimilarity: {score:.3f}\n"
                f"{chunk.text}"
            )

            sources.add(chunk.filename)

        # ==========================================
        # DOCUMENT MODE
        # ==========================================

        if route == "DOCUMENT":

            prompt = f"""
You are an AI Knowledge Assistant.

Use ONLY the uploaded document context.

Instructions:

- Do NOT use outside knowledge.
- If the answer is not available,
say:

"I couldn't find sufficient information in the uploaded documents."

Context:

{context}

Question:

{question}

Answer:
"""

        # ==========================================
        # HYBRID MODE
        # ==========================================

        else:

            prompt = f"""
You are an AI Knowledge Assistant.

Use BOTH:

1. Uploaded document context
2. Your own general knowledge

Rules:

- Prioritize uploaded documents.
- Use general knowledge only to improve explanations.
- Clearly combine both sources.

Document Context:

{context}

Question:

{question}

Answer:
"""

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        return {
            "answer": response.text,
            "sources": list(sources),
        }