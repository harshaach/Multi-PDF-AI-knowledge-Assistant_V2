import argparse
import time
from pathlib import Path

import faiss

from app.services.pdf_service import PDFService
from app.services.embedding_services import EmbeddingService


def main():

    parser = argparse.ArgumentParser(
        description="Inspect retrieved chunks for a single question"
    )

    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to PDF",
    )

    parser.add_argument(
        "--question",
        required=True,
        help="Question to diagnose",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print("=" * 70)
    print("V2 RETRIEVAL DIAGNOSTIC")
    print("=" * 70)

    print(f"\nPDF      : {pdf_path}")
    print(f"Question : {args.question}")
    print(f"Top-K    : {args.top_k}")

    # --------------------------------------------------
    # SERVICES
    # --------------------------------------------------

    pdf_service = PDFService()
    embedding_service = EmbeddingService()

    # --------------------------------------------------
    # LOAD PDF
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("LOADING PDF")
    print("-" * 70)

    start = time.perf_counter()

    document, chunks = pdf_service.extract_chunks(
        pdf_path
    )

    extraction_time = (
        time.perf_counter() - start
    )

    print(f"Document : {document.filename}")
    print(f"Pages    : {document.total_pages}")
    print(f"Chunks   : {len(chunks)}")
    print(
        f"Extraction + chunking: "
        f"{extraction_time:.3f} sec"
    )

    # --------------------------------------------------
    # BUILD INDEX
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("BUILDING FAISS INDEX")
    print("-" * 70)

    start = time.perf_counter()

    embedding_service.add_chunks(chunks)

    indexing_time = (
        time.perf_counter() - start
    )

    print(
        f"Indexing time: "
        f"{indexing_time:.3f} sec"
    )

    print(
        f"FAISS vectors: "
        f"{embedding_service.index.ntotal}"
    )

    # --------------------------------------------------
    # QUERY EMBEDDING
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("SEARCH")
    print("-" * 70)

    start = time.perf_counter()

    query_embedding = embedding_service.model.encode(
        [args.question],
        convert_to_numpy=True,
    )

    faiss.normalize_L2(query_embedding)

    embedding_time = (
        time.perf_counter() - start
    )

    print(
        f"Query embedding time: "
        f"{embedding_time:.4f} sec"
    )

    # --------------------------------------------------
    # RAW FAISS SEARCH
    # --------------------------------------------------

    start = time.perf_counter()

    scores, indices = embedding_service.index.search(
        query_embedding.astype("float32"),
        min(args.top_k, embedding_service.index.ntotal),
    )

    faiss_time = (
        time.perf_counter() - start
    )

    print(
        f"FAISS search time: "
        f"{faiss_time:.6f} sec"
    )

    # --------------------------------------------------
    # DISPLAY CHUNKS
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("RETRIEVED CHUNKS")
    print("=" * 70)

    for rank, (idx, score) in enumerate(
        zip(indices[0], scores[0]),
        start=1,
    ):

        if idx == -1:
            continue

        chunk = embedding_service.chunks[idx]

        print("\n" + "-" * 70)

        print(f"Rank          : {rank}")
        print(f"Score         : {score:.4f}")
        print(f"Filename      : {chunk.filename}")
        print(f"Page          : {chunk.page_number}")
        print(f"Chunk index   : {chunk.chunk_index}")
        print(f"Characters    : {chunk.character_count}")
        print(f"Sentences     : {chunk.sentence_count}")

        print("\nCHUNK TEXT:")
        print(chunk.text)

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()