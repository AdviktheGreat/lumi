"""
Demo: Target Validation Pipeline — Lumi Virtual Lab

Runs a complete target validation analysis for a specified gene and disease
through the full YOHAS orchestration pipeline.

Usage:
    python -m demos.target_validation
    python -m demos.target_validation --target BRCA1 --disease "breast cancer"
    python -m demos.target_validation --target "B7-H3" --disease "lung adenocarcinoma"

Requirements:
    - ANTHROPIC_API_KEY set in the environment (or in .env)
    - Project dependencies installed (see pyproject.toml)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so ``src.*`` imports resolve
# regardless of how/where the script is invoked.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.orchestrator.pipeline import run_yohas_pipeline  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_query(target: str, disease: str) -> str:
    """Assemble the natural-language query for the pipeline."""
    return (
        f"Evaluate {target} as a therapeutic target for {disease}. "
        f"Assess genetic evidence, expression patterns, safety profile, "
        f"existing drugs, and clinical trial landscape."
    )


def _print_section(title: str, width: int = 70) -> None:
    print(f"\n--- {title} ---")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(
    target: str,
    disease: str,
    cost_ceiling: float = 50.0,
) -> object:
    """Run a target validation analysis through the full pipeline.

    Parameters
    ----------
    target:
        Gene or protein target name (e.g. ``"BRCA1"``, ``"B7-H3"``).
    disease:
        Disease or indication (e.g. ``"breast cancer"``).
    cost_ceiling:
        Maximum spend in USD for the pipeline run.

    Returns
    -------
    FinalReport
        The structured report produced by the YOHAS pipeline.
    """
    # --- logging setup ---
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("demo.target_validation")

    query = _build_query(target, disease)

    logger.info("=" * 70)
    logger.info("LUMI VIRTUAL LAB — Target Validation Demo")
    logger.info("=" * 70)
    logger.info("Target:        %s", target)
    logger.info("Disease:       %s", disease)
    logger.info("Cost ceiling:  $%.2f", cost_ceiling)
    logger.info("Query:         %s", query)
    logger.info("=" * 70)

    # --- initialise divisions (if factory exists) ---
    divisions = None
    try:
        from src.factory import create_system  # type: ignore[import-untyped]

        logger.info("Initializing agent swarm via factory...")
        divisions = create_system()
        logger.info("System ready — %d divisions loaded.", len(divisions))
    except ImportError:
        logger.warning(
            "src.factory not found — running pipeline without pre-built divisions."
        )

    # --- execute the pipeline ---
    logger.info("Launching YOHAS pipeline...")
    report = await run_yohas_pipeline(
        user_query=query,
        divisions=divisions,
        cost_ceiling=cost_ceiling,
        enable_world_model=True,
    )

    # --- print results ---
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(f"\nQuery ID:  {report.query_id}")
    print(f"Duration:  {report.total_duration_seconds:.1f}s")
    print(f"Cost:      ${report.total_cost:.4f}")

    _print_section("Executive Summary")
    print(report.executive_summary or "(no summary)")

    if report.key_findings:
        _print_section(f"Key Findings ({len(report.key_findings)})")
        for i, finding in enumerate(report.key_findings, 1):
            conf = finding.confidence.level.value
            print(f"  {i}. [{conf}] {finding.claim_text}")

    if report.risk_assessment:
        _print_section("Risk Assessment")
        for key, val in report.risk_assessment.items():
            print(f"  {key}: {val}")

    if report.limitations:
        _print_section("Limitations")
        for lim in report.limitations:
            print(f"  - {lim}")

    if report.recommended_experiments:
        _print_section(
            f"Recommended Experiments ({len(report.recommended_experiments)})"
        )
        for exp in report.recommended_experiments:
            title = (
                exp.get("title", "Untitled") if isinstance(exp, dict) else str(exp)
            )
            print(f"  - {title}")

    # --- persist full report to disk ---
    output_dir = os.path.join(_PROJECT_ROOT, "data", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{report.query_id}.json")
    with open(output_path, "w") as fh:
        json.dump(report.model_dump(mode="json"), fh, indent=2, default=str)
    print(f"\nFull report saved to: {output_path}")

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lumi Virtual Lab — Target Validation Demo",
    )
    parser.add_argument(
        "--target", default="BRCA1", help="Gene/protein target (default: BRCA1)",
    )
    parser.add_argument(
        "--disease", default="breast cancer",
        help='Disease or indication (default: "breast cancer")',
    )
    parser.add_argument(
        "--cost-ceiling", type=float, default=50.0,
        help="Maximum spend in USD (default: 50.0)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.target, args.disease, args.cost_ceiling))
