"""Script to benchmark Google Gemini response latency and throughput."""

from __future__ import annotations

import asyncio
import os
import sys
import time

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.services.llm_service import LLMService


async def run_single_benchmark(llm: LLMService, benchmark_id: int) -> dict:
    prompt = "Give a 3-sentence summary of the database concept RAG (Retrieval-Augmented Generation)."
    start_time = time.perf_counter()
    try:
        response = await llm.generate(prompt)
        elapsed = time.perf_counter() - start_time
        tokens = len(response.split()) * 1.3  # rough token count
        tps = tokens / elapsed if elapsed > 0 else 0
        return {
            "id": benchmark_id,
            "status": "success",
            "latency_sec": round(elapsed, 2),
            "approx_tokens": round(tokens),
            "tokens_per_sec": round(tps, 1),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            "id": benchmark_id,
            "status": "failed",
            "latency_sec": round(elapsed, 2),
            "error": str(e),
        }


async def main() -> None:
    settings = get_settings()
    
    print("=" * 60)
    print("Google Gemini Model Performance Benchmark")
    print(f"Model: {settings.GEMINI_MODEL}")
    print("=" * 60)

    llm = LLMService(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
    )

    print("Running sequential benchmark (3 iterations)...")
    results = []
    for i in range(3):
        print(f"Running iteration {i+1}...")
        res = await run_single_benchmark(llm, i + 1)
        results.append(res)
        print(f"  Iteration {i+1} completed in {res['latency_sec']}s ({res.get('tokens_per_sec', 0)} tok/s)")
        await asyncio.sleep(1)

    print("\nRunning concurrent benchmark (3 simultaneous requests)...")
    start_time = time.perf_counter()
    concurrent_results = await asyncio.gather(
        run_single_benchmark(llm, 4),
        run_single_benchmark(llm, 5),
        run_single_benchmark(llm, 6),
    )
    total_time = time.perf_counter() - start_time
    print(f"Concurrent execution completed in {total_time:.2f}s")
    
    results.extend(concurrent_results)

    successes = [r for r in results if r["status"] == "success"]
    if successes:
        avg_lat = sum(r["latency_sec"] for r in successes) / len(successes)
        avg_tps = sum(r["tokens_per_sec"] for r in successes) / len(successes)
        print("\nBENCHMARK RESULTS SUMMARY:")
        print("-" * 40)
        print(f"Successful Requests:  {len(successes)} / {len(results)}")
        print(f"Average Latency:      {avg_lat:.2f} seconds")
        print(f"Average Throughput:   {avg_tps:.1f} tokens/second")
        print("-" * 40)
    else:
        print("\nAll benchmark requests failed.")


if __name__ == "__main__":
    asyncio.run(main())
