import argparse
import time
from pathlib import Path

import faiss
import numpy as np

from app.services.pdf_service import PDFService
from app.services.embedding_services import EmbeddingService


# ============================================================
# DOCUMENT-RELEVANT QUESTIONS
# ============================================================

DOCUMENT_QUESTIONS = [

    # --------------------------------------------------------
    # FASTAPI — 20 QUESTIONS
    # --------------------------------------------------------

    ("fastapi", "What is FastAPI?"),
    ("fastapi", "Why is FastAPI considered fast?"),
    ("fastapi", "How do I create a FastAPI application?"),
    ("fastapi", "How do I define a GET endpoint?"),
    ("fastapi", "What does @app.get() do?"),
    ("fastapi", "How do I define a POST endpoint?"),
    ("fastapi", "What is Uvicorn used for?"),
    ("fastapi", "How do I run a FastAPI application?"),
    ("fastapi", "How are path parameters handled?"),
    ("fastapi", "How are query parameters defined?"),
    ("fastapi", "How does FastAPI use Python type hints?"),
    ("fastapi", "How does request validation work?"),
    ("fastapi", "How do I define request body data?"),
    ("fastapi", "How does FastAPI generate API documentation?"),
    ("fastapi", "What is the purpose of Pydantic in FastAPI?"),
    ("fastapi", "How do I return data from a FastAPI endpoint?"),
    ("fastapi", "How do I handle different HTTP methods in FastAPI?"),
    ("fastapi", "How can I make a FastAPI endpoint asynchronous?"),
    ("fastapi", "What are the main advantages of FastAPI?"),
    ("fastapi", "How does FastAPI support response models?"),

    # --------------------------------------------------------
    # JAVASCRIPT — 20 QUESTIONS
    # --------------------------------------------------------

    ("javascript", "What is JavaScript?"),
    ("javascript", "What are the main advantages of JavaScript?"),
    ("javascript", "What is client-side JavaScript?"),
    ("javascript", "How is JavaScript included in an HTML document?"),
    ("javascript", "What are JavaScript variables?"),
    ("javascript", "What are the different JavaScript data types?"),
    ("javascript", "What is variable scope in JavaScript?"),
    ("javascript", "What are JavaScript operators?"),
    ("javascript", "How does the if-else statement work in JavaScript?"),
    ("javascript", "How does the switch-case statement work in JavaScript?"),
    ("javascript", "How does the while loop work in JavaScript?"),
    ("javascript", "How does the for loop work in JavaScript?"),
    ("javascript", "How is a function defined in JavaScript?"),
    ("javascript", "How are parameters passed to a JavaScript function?"),
    ("javascript", "What is the return statement used for in JavaScript?"),
    ("javascript", "What are JavaScript events?"),
    ("javascript", "What is the onclick event in JavaScript?"),
    ("javascript", "What are cookies in JavaScript?"),
    ("javascript", "How does JavaScript perform page redirection?"),
    ("javascript", "How are objects and object methods used in JavaScript?"),
]


# ============================================================
# UNRELATED QUESTIONS
# ============================================================

GENERAL_QUESTIONS = [
    "What is the capital of Japan?",
    "Explain how photosynthesis works.",
    "Who invented the telephone?",
    "What is machine learning?",
    "What causes earthquakes?",
    "Explain the water cycle.",
    "What is the largest planet in the solar system?",
    "How does TCP establish a connection?",
    "What is a binary search tree?",
    "How does a solar panel generate electricity?",
    "What is blockchain?",
    "Explain Newton's laws of motion.",
    "How does a database index work?",
    "What is the difference between RAM and ROM?",
    "How does an operating system manage memory?",
    "What is the theory of relativity?",
    "How does a CPU execute instructions?",
    "What is quantum computing?",
    "How does DNA replication work?",
    "What is the greenhouse effect?",
    "What is the speed of light?",
    "How does the human digestive system work?",
    "What is artificial intelligence?",
    "How do airplanes fly?",
    "What is the boiling point of water?",
    "How does a refrigerator work?",
    "What is the difference between weather and climate?",
    "What is gravitational force?",
    "How does electricity flow through a circuit?",
    "What is the structure of an atom?",
    "How does a neural network work?",
    "What is the Milky Way?",
    "How do vaccines work?",
    "What is natural language processing?",
    "How does a combustion engine work?",
    "What is the difference between mass and weight?",
    "How does the immune system work?",
    "What is plate tectonics?",
    "How does GPS determine location?",
    "What is the ozone layer?",
]


# ============================================================
# THRESHOLDS
# ============================================================

THRESHOLDS = [
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
]


# ============================================================
# LOAD PDF INTO INDEX
# ============================================================

def load_pdf(
    pdf_service,
    embedding_service,
    pdf_path,
    label,
):
    print("\n" + "-" * 70)
    print(f"Loading {label.upper()} PDF")
    print("-" * 70)

    start = time.perf_counter()

    document, chunks = pdf_service.extract_chunks(
        pdf_path
    )

    extraction_time = time.perf_counter() - start

    print(f"Document : {document.filename}")
    print(f"Pages    : {document.total_pages}")
    print(f"Chunks   : {len(chunks)}")
    print(
        f"Extraction + chunking: "
        f"{extraction_time:.3f} sec"
    )

    start = time.perf_counter()

    embedding_service.add_chunks(chunks)

    indexing_time = time.perf_counter() - start

    print(
        f"Indexing time: "
        f"{indexing_time:.3f} sec"
    )

    return document, chunks


# ============================================================
# RAW TOP-1 SEARCH
# ============================================================

def get_raw_top_score(
    embedding_service,
    question,
):
    """
    Get the raw top-1 FAISS similarity score.

    This deliberately bypasses EmbeddingService.search()
    because production search applies the current threshold.
    Calibration needs the raw score.
    """

    start = time.perf_counter()

    query_embedding = embedding_service.model.encode(
        [question],
        convert_to_numpy=True,
    )

    faiss.normalize_L2(query_embedding)

    scores, indices = embedding_service.index.search(
        query_embedding.astype(np.float32),
        1,
    )

    latency = time.perf_counter() - start

    top_score = float(scores[0][0])
    top_index = int(indices[0][0])

    return top_score, top_index, latency


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    results,
    threshold,
):
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for result in results:

        actual = result["expected_relevant"]

        predicted = (
            result["top_score"] >= threshold
        )

        if predicted and actual:
            tp += 1

        elif predicted and not actual:
            fp += 1

        elif not predicted and not actual:
            tn += 1

        elif not predicted and actual:
            fn += 1

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    accuracy = (
        (tp + tn) / len(results)
        if results
        else 0.0
    )

    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Multi-PDF FAISS retrieval "
            "threshold calibration"
        )
    )

    parser.add_argument(
        "--fastapi-pdf",
        required=True,
        help="Path to FastAPI PDF",
    )

    parser.add_argument(
        "--javascript-pdf",
        required=True,
        help="Path to JavaScript PDF",
    )

    args = parser.parse_args()

    fastapi_path = Path(args.fastapi_pdf)
    javascript_path = Path(args.javascript_pdf)

    if not fastapi_path.exists():
        raise FileNotFoundError(
            f"FastAPI PDF not found: {fastapi_path}"
        )

    if not javascript_path.exists():
        raise FileNotFoundError(
            f"JavaScript PDF not found: {javascript_path}"
        )

    print("=" * 70)
    print("MULTI-PDF RETRIEVAL THRESHOLD CALIBRATION")
    print("=" * 70)

    print("\nDataset:")
    print("  FastAPI relevant questions : 20")
    print("  JavaScript relevant        : 20")
    print("  Unrelated questions        : 40")
    print("  Total evaluation queries   : 80")

    # ========================================================
    # SERVICES
    # ========================================================

    pdf_service = PDFService()

    embedding_service = EmbeddingService()

    # ========================================================
    # LOAD BOTH PDFs INTO SAME FAISS INDEX
    # ========================================================

    load_pdf(
        pdf_service,
        embedding_service,
        fastapi_path,
        "FastAPI",
    )

    load_pdf(
        pdf_service,
        embedding_service,
        javascript_path,
        "JavaScript",
    )

    print("\n" + "=" * 70)
    print("COMBINED FAISS INDEX")
    print("=" * 70)

    print(
        f"Total FAISS vectors: "
        f"{embedding_service.index.ntotal}"
    )

    # ========================================================
    # COLLECT RESULTS
    # ========================================================

    results = []

    print("\n" + "=" * 70)
    print("DOCUMENT-RELEVANT QUESTIONS")
    print("=" * 70)

    for label, question in DOCUMENT_QUESTIONS:

        score, index, latency = get_raw_top_score(
            embedding_service,
            question,
        )

        result = {
            "category": label,
            "question": question,
            "expected_relevant": True,
            "top_score": score,
            "latency_ms": latency * 1000,
        }

        results.append(result)

        print(
            f"\n[{label.upper()}]"
            f"\nQuestion: {question}"
            f"\nTop score: {score:.4f}"
            f"\nLatency: {latency * 1000:.3f} ms"
        )

    # ========================================================
    # GENERAL QUESTIONS
    # ========================================================

    print("\n" + "=" * 70)
    print("GENERAL / UNRELATED QUESTIONS")
    print("=" * 70)

    for question in GENERAL_QUESTIONS:

        score, index, latency = get_raw_top_score(
            embedding_service,
            question,
        )

        result = {
            "category": "general",
            "question": question,
            "expected_relevant": False,
            "top_score": score,
            "latency_ms": latency * 1000,
        }

        results.append(result)

        print(
            f"\n[GENERAL]"
            f"\nQuestion: {question}"
            f"\nTop score: {score:.4f}"
            f"\nLatency: {latency * 1000:.3f} ms"
        )

    # ========================================================
    # THRESHOLD EVALUATION
    # ========================================================

    print("\n" + "=" * 70)
    print("THRESHOLD EVALUATION")
    print("=" * 70)

    print(
        "\n"
        "Threshold | TP | FP | TN | FN | "
        "Precision | Recall | F1 | Accuracy"
    )

    print("-" * 70)

    metrics = []

    for threshold in THRESHOLDS:

        result = calculate_metrics(
            results,
            threshold,
        )

        metrics.append(result)

        print(
            f"{result['threshold']:.2f}"
            f"       | "
            f"{result['tp']:2d} | "
            f"{result['fp']:2d} | "
            f"{result['tn']:2d} | "
            f"{result['fn']:2d} | "
            f"{result['precision'] * 100:8.2f}% | "
            f"{result['recall'] * 100:6.2f}% | "
            f"{result['f1']:.3f} | "
            f"{result['accuracy'] * 100:7.2f}%"
        )

    # ========================================================
    # BEST THRESHOLD
    # ========================================================

    best = max(
        metrics,
        key=lambda item: (
            item["f1"],
            item["recall"],
            item["precision"],
        ),
    )

    print("\n" + "=" * 70)
    print("BEST CALIBRATION RESULT")
    print("=" * 70)

    print(
        f"Threshold : {best['threshold']:.2f}"
    )

    print(
        f"TP        : {best['tp']}"
    )

    print(
        f"FP        : {best['fp']}"
    )

    print(
        f"TN        : {best['tn']}"
    )

    print(
        f"FN        : {best['fn']}"
    )

    print(
        f"Precision : "
        f"{best['precision'] * 100:.2f}%"
    )

    print(
        f"Recall    : "
        f"{best['recall'] * 100:.2f}%"
    )

    print(
        f"F1        : "
        f"{best['f1']:.3f}"
    )

    print(
        f"Accuracy  : "
        f"{best['accuracy'] * 100:.2f}%"
    )

    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()