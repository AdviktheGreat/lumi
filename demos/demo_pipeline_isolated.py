"""Isolated test script for the YOHAS pipeline.

Run:  ANTHROPIC_API_KEY=sk-... python -m tests.test_pipeline_isolated

Uses dynamic SubLab mode (no static agent roster needed).
Prints progress and final report to stdout.
"""

import asyncio
import logging
import os
import sys
import time

# Setup logging so you can see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-30s %(levelname)-5s %(message)s",
    datefmt="%H:%M:%S",
)

# Suppress noisy third-party loggers
for name in ["httpx", "httpcore", "anthropic"]:
    logging.getLogger(name).setLevel(logging.WARNING)

log = logging.getLogger("test")


async def run():
    # Verify API key
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    print(f"API key: ...{key[-8:]}")

    from src.orchestrator.pipeline import run_yohas_pipeline

    query = (
        "Assess whether repurposing GLP-1 receptor agonists (e.g., semaglutide) "
        "could slow neurodegeneration in early-stage Parkinson's disease. "
        "Map the GLP-1R neuroprotective signaling pathway and evaluate the "
        "available clinical and genetic evidence."
    )

    print(f"\n{'='*60}")
    print(f"Query: {query[:80]}...")
    print(f"Mode: Dynamic SubLab")
    print(f"World Model: disabled")
    print(f"{'='*60}\n")

    start = time.time()

    report = await run_yohas_pipeline(
        user_query=query,
        dynamic=True,
        enable_world_model=False,
        cost_ceiling=10.0,
    )

    elapsed = time.time() - start

    # Print results
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Duration: {elapsed:.1f}s")
    print(f"Cost: ${report.total_cost:.4f}")
    print(f"Query ID: {report.query_id}")
    print(f"Findings: {len(report.key_findings)}")
    print(f"Limitations: {len(report.limitations)}")

    print(f"\n--- Executive Summary ---")
    print(report.executive_summary[:500] if report.executive_summary else "(empty)")

    if report.key_findings:
        print(f"\n--- Key Findings ({len(report.key_findings)}) ---")
        for i, claim in enumerate(report.key_findings[:5], 1):
            conf = f"{claim.confidence.level.value} {claim.confidence.score:.0%}"
            print(f"  {i}. [{conf}] {claim.claim_text[:100]}")
            print(f"     Agent: {claim.agent_id} | Evidence: {len(claim.supporting_evidence)} sources")

    if report.biosecurity_clearance:
        bc = report.biosecurity_clearance
        print(f"\n--- Biosecurity ---")
        print(f"  Category: {bc.category.value} | Veto: {bc.veto}")

    if report.hitl_summary:
        print(f"\n--- HITL Summary ---")
        print(f"  {report.hitl_summary[:200]}")

    if report.living_document_markdown:
        print(f"\n--- Living Document (first 500 chars) ---")
        print(report.living_document_markdown[:500])

    print(f"\n{'='*60}")
    print(f"Total cost: ${report.total_cost:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(run())
