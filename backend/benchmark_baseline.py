import argparse
import json
import statistics
import time
from pathlib import Path

import psutil
import requests


def percentile(values, p):
    values = sorted(values)
    index = int((len(values) - 1) * p / 100)
    return values[index]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--chat-id", default="baseline-test")
    parser.add_argument("--queries", nargs="+", required=True)
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    process = psutil.Process()

    print("=" * 60)
    print("MULTI-PDF RAG — V2 BASELINE BENCHMARK")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Health check
    # ---------------------------------------------------------
    response = requests.get(f"{base_url}/health", timeout=30)
    response.raise_for_status()

    print("\n[1] Health check")
    print(response.json())

    # ---------------------------------------------------------
    # 2. Memory before ingestion
    # ---------------------------------------------------------
    memory_before = process.memory_info().rss / (1024 * 1024)

    # ---------------------------------------------------------
    # 3. PDF ingestion
    # ---------------------------------------------------------
    print("\n[2] PDF ingestion")

    start = time.perf_counter()

    with pdf_path.open("rb") as f:
        response = requests.post(
            f"{base_url}/upload",
            params={"chat_id": args.chat_id},
            files={
                "files": (
                    pdf_path.name,
                    f,
                    "application/pdf",
                )
            },
            timeout=600,
        )

    ingestion_time = time.perf_counter() - start

    response.raise_for_status()

    memory_after = process.memory_info().rss / (1024 * 1024)

    upload_result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Ingestion time: {ingestion_time:.3f} sec")
    print(f"Memory before: {memory_before:.2f} MB")
    print(f"Memory after:  {memory_after:.2f} MB")
    print(f"Memory increase: {memory_after - memory_before:.2f} MB")
    print(f"Upload result: {json.dumps(upload_result, indent=2)}")

    # ---------------------------------------------------------
    # 4. Query benchmark
    # ---------------------------------------------------------
    print("\n[3] Query benchmark")

    query_times = []

    for i, question in enumerate(args.queries, start=1):

        start = time.perf_counter()

        response = requests.post(
            f"{base_url}/query",
            params={"chat_id": args.chat_id},
            json={
                "question": question,
                "top_k": 5,
            },
            timeout=300,
        )

        elapsed = time.perf_counter() - start

        response.raise_for_status()

        query_times.append(elapsed)

        result = response.json()

        print(f"\nQuery {i}")
        print(f"Question: {question}")
        print(f"Latency: {elapsed:.3f} sec")
        print(f"Sources: {result.get('sources', [])}")
        print(f"Answer preview: {result.get('answer', '')[:200]}")

    # ---------------------------------------------------------
    # 5. Documents
    # ---------------------------------------------------------
    response = requests.get(
        f"{base_url}/documents",
        params={"chat_id": args.chat_id},
        timeout=30,
    )

    response.raise_for_status()

    documents = response.json()

    # ---------------------------------------------------------
    # 6. Final report
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("BASELINE RESULTS")
    print("=" * 60)

    print(f"PDF: {pdf_path.name}")
    print(f"Documents: {documents.get('documents', [])}")

    print(f"\nIngestion:")
    print(f"  Time: {ingestion_time:.3f} sec")

    print(f"\nMemory:")
    print(f"  Before: {memory_before:.2f} MB")
    print(f"  After:  {memory_after:.2f} MB")
    print(f"  Increase: {memory_after - memory_before:.2f} MB")

    print(f"\nQuery latency:")
    print(f"  Average: {statistics.mean(query_times):.3f} sec")
    print(f"  Median:  {statistics.median(query_times):.3f} sec")
    print(f"  P95:     {percentile(query_times, 95):.3f} sec")
    print(f"  Min:     {min(query_times):.3f} sec")
    print(f"  Max:     {max(query_times):.3f} sec")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()