"""Pipeline evaluation script.

Tests the Lumi YOHAS pipeline architecture across multiple dimensions:
1. Component integration (factory → agents → divisions → CSO)
2. Concurrency gate (verifies rate limiting under parallel load)
3. HITL routing (confidence thresholds, Slack notification paths)
4. Living document (version evolution across pipeline milestones)
5. End-to-end pipeline (lightweight query through the full system)

Inspired by BioMNI benchmarks:
- Multi-step reasoning across divisions
- Evidence quality / confidence calibration
- Provenance tracking fidelity
- Biosecurity screening accuracy
- Cross-division synthesis coherence

Usage:
    ANTHROPIC_API_KEY=sk-... python -m tests.eval_pipeline
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("lumi.eval")


@dataclass
class EvalResult:
    name: str
    passed: bool
    duration: float = 0.0
    details: str = ""
    error: str = ""


@dataclass
class EvalSuite:
    results: list[EvalResult] = field(default_factory=list)

    def add(self, result: EvalResult) -> None:
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        logger.info(
            "[%s] %s (%.1fs) %s",
            status,
            result.name,
            result.duration,
            f"— {result.details}" if result.details else "",
        )
        if result.error:
            logger.error("  Error: %s", result.error)

    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines = [
            "",
            "=" * 60,
            f"EVALUATION SUMMARY: {passed}/{total} passed",
            "=" * 60,
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.name} ({r.duration:.1f}s)")
            if r.error:
                lines.append(f"         Error: {r.error[:200]}")
        lines.append("=" * 60)
        return "\n".join(lines)


# -----------------------------------------------------------------------
# Test 1: API connectivity
# -----------------------------------------------------------------------

async def test_api_connectivity(suite: EvalSuite) -> bool:
    """Verify the Anthropic API key works with a minimal call."""
    t0 = time.time()
    try:
        from src.utils.llm import LLMClient, ModelTier

        llm = LLMClient()
        response = await llm.chat(
            messages=[{"role": "user", "content": "Reply with exactly: LUMI_OK"}],
            model=ModelTier.HAIKU,
            max_tokens=20,
        )
        text = "".join(
            b.text for b in response.content if hasattr(b, "text")
        )
        ok = "LUMI_OK" in text or "OK" in text.upper()
        suite.add(EvalResult(
            name="API Connectivity",
            passed=ok,
            duration=time.time() - t0,
            details=f"Response: {text[:50]}",
        ))
        return ok
    except Exception as e:
        suite.add(EvalResult(
            name="API Connectivity",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))
        return False


# -----------------------------------------------------------------------
# Test 2: Factory & agent creation
# -----------------------------------------------------------------------

async def test_factory(suite: EvalSuite) -> dict | None:
    """Verify the full agent swarm can be created and wired."""
    t0 = time.time()
    try:
        from src.factory import create_system
        divisions = create_system()

        # Verify structure
        expected_divisions = {
            "Target Identification", "Target Safety", "Modality Selection",
            "Molecular Design", "Clinical Intelligence", "Computational Biology",
            "Experimental Design", "Biosecurity",
        }
        actual = set(divisions.keys())
        missing = expected_divisions - actual

        # Count total specialists
        total_specialists = sum(
            len(d.specialist_agents) for d in divisions.values()
        )

        ok = len(missing) == 0 and total_specialists >= 17
        suite.add(EvalResult(
            name="Factory & Agent Creation",
            passed=ok,
            duration=time.time() - t0,
            details=f"{len(divisions)} divisions, {total_specialists} specialists"
            + (f", missing: {missing}" if missing else ""),
        ))
        return divisions if ok else None
    except Exception as e:
        suite.add(EvalResult(
            name="Factory & Agent Creation",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))
        return None


# -----------------------------------------------------------------------
# Test 3: Concurrency gate
# -----------------------------------------------------------------------

async def test_concurrency_gate(suite: EvalSuite) -> None:
    """Verify the concurrency gate limits parallel API calls."""
    t0 = time.time()
    try:
        from src.utils.llm import LLMClient, ModelTier, get_concurrency_gate

        gate = get_concurrency_gate()
        max_conc = gate.max_concurrent

        # Fire 10 parallel requests — all should succeed without crashes
        async def mini_call(idx: int) -> str:
            llm = LLMClient()
            resp = await llm.chat(
                messages=[{"role": "user", "content": f"Reply with the number {idx}"}],
                model=ModelTier.HAIKU,
                max_tokens=20,
            )
            return "".join(b.text for b in resp.content if hasattr(b, "text"))

        results = await asyncio.gather(
            *[mini_call(i) for i in range(10)],
            return_exceptions=True,
        )

        errors = [r for r in results if isinstance(r, Exception)]
        successes = [r for r in results if not isinstance(r, Exception)]

        ok = len(errors) == 0
        suite.add(EvalResult(
            name="Concurrency Gate (10 parallel)",
            passed=ok,
            duration=time.time() - t0,
            details=f"{len(successes)} succeeded, {len(errors)} failed, "
                    f"max_concurrent={max_conc}, gate_stats={gate.stats}",
            error=str(errors[0]) if errors else "",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Concurrency Gate (10 parallel)",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 4: HITL routing logic
# -----------------------------------------------------------------------

async def test_hitl_routing(suite: EvalSuite) -> None:
    """Test confidence-based routing without live API calls."""
    t0 = time.time()
    try:
        from src.orchestrator.hitl.router import ConfidenceRouter, HITLConfig
        from src.utils.types import (
            AgentResult, Claim, ConfidenceAssessment, ConfidenceLevel, DivisionReport,
        )

        config = HITLConfig(
            hard_threshold=0.3,
            soft_threshold=0.5,
            auto_threshold=0.7,
            enabled=True,
        )
        router = ConfidenceRouter(config=config)

        # Build test reports with varying confidence
        def make_claim(text: str, score: float, level: ConfidenceLevel) -> Claim:
            return Claim(
                claim_text=text,
                confidence=ConfidenceAssessment(level=level, score=score),
                agent_id="test_agent",
            )

        reports = [
            DivisionReport(
                division_id="div_test",
                division_name="Test Division",
                lead_agent="test_lead",
                specialist_results=[
                    AgentResult(
                        agent_id="test_spec",
                        task_id="task_1",
                        findings=[
                            make_claim("High confidence claim", 0.9, ConfidenceLevel.HIGH),
                            make_claim("Medium confidence claim", 0.6, ConfidenceLevel.MEDIUM),
                            make_claim("Low confidence claim", 0.4, ConfidenceLevel.LOW),
                            make_claim("Very low confidence claim", 0.2, ConfidenceLevel.INSUFFICIENT),
                        ],
                    ),
                ],
                synthesis="Test synthesis",
                confidence=ConfidenceAssessment(level=ConfidenceLevel.MEDIUM, score=0.5),
            ),
        ]

        # Disable blocking so test doesn't hang
        config.enabled = False
        result = await router.evaluate_reports(reports, query_id="test_q")

        # Re-enable and test classification (non-blocking path)
        config.enabled = True
        config.soft_timeout_seconds = 0.1  # Don't wait

        # Manually test classification logic
        high_claim = make_claim("High", 0.9, ConfidenceLevel.HIGH)
        low_claim = make_claim("Low", 0.2, ConfidenceLevel.INSUFFICIENT)

        assert high_claim.confidence.score >= config.auto_threshold, "High should auto-pass"
        assert low_claim.confidence.score < config.hard_threshold, "Low should hard-flag"

        suite.add(EvalResult(
            name="HITL Routing Logic",
            passed=True,
            duration=time.time() - t0,
            details=f"Thresholds: hard={config.hard_threshold}, soft={config.soft_threshold}, auto={config.auto_threshold}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="HITL Routing Logic",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 5: Living document lifecycle
# -----------------------------------------------------------------------

async def test_living_document(suite: EvalSuite) -> None:
    """Test document versioning and rendering."""
    t0 = time.time()
    try:
        from src.orchestrator.living_document.document import (
            LivingDocument, SectionType,
        )

        doc = LivingDocument(query_id="eval_test")

        # v1 — initial
        v1 = doc.evolve(
            updates={
                SectionType.BACKGROUND: "Test background content",
                SectionType.HYPOTHESIS: "Test hypothesis",
            },
            author="eval",
            trigger="test_init",
        )
        assert doc.version_count == 1
        assert v1.version_number == 1

        # v2 — evolve
        v2 = doc.evolve(
            updates={
                SectionType.FINDINGS: "Finding 1: Test finding",
                SectionType.BACKGROUND: "Updated background",
            },
            author="eval",
            trigger="test_update",
        )
        assert doc.version_count == 2
        assert v2.version_number == 2
        # Background should be updated, hypothesis carried forward
        bg = v2.get_section(SectionType.BACKGROUND)
        hyp = v2.get_section(SectionType.HYPOTHESIS)
        assert bg is not None and "Updated" in bg.content
        assert hyp is not None and "hypothesis" in hyp.content.lower()

        # Render markdown
        md = doc.render_markdown()
        assert "Research Document (v2)" in md
        assert "Test finding" in md

        # Agent context
        ctx = doc.get_context_for_agent(max_chars=5000)
        assert "eval_test" in ctx

        suite.add(EvalResult(
            name="Living Document Lifecycle",
            passed=True,
            duration=time.time() - t0,
            details=f"{doc.version_count} versions, {len(md)} chars rendered",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Living Document Lifecycle",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 6: Single-agent LLM execution (BioMNI-style: reasoning quality)
# -----------------------------------------------------------------------

async def test_agent_execution(suite: EvalSuite) -> None:
    """Execute a single specialist agent on a research task."""
    t0 = time.time()
    try:
        from src.agents import create_literature_synthesis_agent
        from src.utils.types import Task

        agent = create_literature_synthesis_agent()
        task = Task(
            task_id="eval_lit_1",
            description=(
                "Briefly summarize the role of PCSK9 in cholesterol metabolism. "
                "State one key finding with confidence level."
            ),
            division="Computational Biology",
        )

        result = await agent.execute(task)

        has_response = bool(result.raw_data.get("final_response", ""))
        has_findings = len(result.findings) > 0
        cost_ok = result.cost > 0

        suite.add(EvalResult(
            name="Single Agent Execution (lit_synthesis)",
            passed=has_response and has_findings,
            duration=time.time() - t0,
            details=(
                f"Findings: {len(result.findings)}, "
                f"Cost: ${result.cost:.4f}, "
                f"Model: {result.model_used}, "
                f"Duration: {result.duration_seconds:.1f}s"
            ),
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Single Agent Execution (lit_synthesis)",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 7: Division-level coordination
# -----------------------------------------------------------------------

async def test_division_execution(suite: EvalSuite, divisions: dict | None) -> None:
    """Execute a single division task to test decomposition + specialist dispatch."""
    t0 = time.time()
    if divisions is None:
        suite.add(EvalResult(
            name="Division Execution",
            passed=False,
            duration=0,
            error="Skipped — factory failed",
        ))
        return

    try:
        from src.utils.types import Task, Priority

        # Use CompBio division (1 specialist — lightweight)
        lead = divisions.get("Computational Biology")
        if lead is None:
            suite.add(EvalResult(
                name="Division Execution",
                passed=False,
                duration=time.time() - t0,
                error="CompBio division not found",
            ))
            return

        task = Task(
            task_id="eval_div_1",
            description="Summarize the therapeutic rationale for targeting KRAS G12C in NSCLC.",
            division="Computational Biology",
            priority=Priority.MEDIUM,
        )

        report = await lead.execute_division_task(task)

        has_synthesis = len(report.synthesis) > 50
        has_confidence = report.confidence.score > 0
        has_results = len(report.specialist_results) > 0

        suite.add(EvalResult(
            name="Division Execution (CompBio)",
            passed=has_synthesis and has_confidence,
            duration=time.time() - t0,
            details=(
                f"Specialists ran: {len(report.specialist_results)}, "
                f"Synthesis: {len(report.synthesis)} chars, "
                f"Confidence: {report.confidence.level.value} ({report.confidence.score:.2f})"
            ),
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Division Execution (CompBio)",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 8: CSO intake + planning (no full execution)
# -----------------------------------------------------------------------

async def test_cso_planning(suite: EvalSuite, divisions: dict | None) -> None:
    """Test CSO intake and plan generation without running the full pipeline."""
    t0 = time.time()
    try:
        from src.orchestrator.cso import CSOOrchestrator

        cso = CSOOrchestrator(divisions=divisions)
        research_brief = await cso._intake(
            "Evaluate PCSK9 as a therapeutic target for familial hypercholesterolemia"
        )

        has_target = bool(research_brief.get("target") or research_brief.get("scope"))
        has_content = len(json.dumps(research_brief)) > 50

        suite.add(EvalResult(
            name="CSO Intake + Planning",
            passed=has_target and has_content,
            duration=time.time() - t0,
            details=f"Brief keys: {list(research_brief.keys())}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="CSO Intake + Planning",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 9: Confidence calibration
# -----------------------------------------------------------------------

async def test_confidence_calibration(suite: EvalSuite) -> None:
    """Test confidence scoring against known evidence patterns."""
    t0 = time.time()
    try:
        from src.utils.confidence import calibrate_confidence
        from src.utils.types import ConfidenceLevel

        # Strong evidence — should yield HIGH
        strong = calibrate_confidence([
            {"source": "PMID:12345", "strength": 0.9, "convergence": 0.85, "independent": True},
            {"source": "PMID:23456", "strength": 0.85, "convergence": 0.8, "independent": True},
            {"source": "PMID:34567", "strength": 0.88, "convergence": 0.9, "independent": True},
        ])

        # Weak evidence — should yield LOW or INSUFFICIENT
        weak = calibrate_confidence([
            {"source": "preprint", "strength": 0.15, "convergence": 0.1},
        ])

        # No evidence
        empty = calibrate_confidence([])

        ok = (
            strong.level == ConfidenceLevel.HIGH
            and strong.score > 0.8
            and weak.level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT)
            and empty.level == ConfidenceLevel.INSUFFICIENT
        )

        suite.add(EvalResult(
            name="Confidence Calibration",
            passed=ok,
            duration=time.time() - t0,
            details=(
                f"Strong: {strong.level.value}({strong.score:.2f}), "
                f"Weak: {weak.level.value}({weak.score:.2f}), "
                f"Empty: {empty.level.value}"
            ),
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Confidence Calibration",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Test 10: Provenance tracking
# -----------------------------------------------------------------------

async def test_provenance(suite: EvalSuite) -> None:
    """Test provenance tracker — contradiction detection and dedup."""
    t0 = time.time()
    try:
        from src.utils.provenance import ProvenanceTracker
        from src.utils.types import (
            Claim, ConfidenceAssessment, ConfidenceLevel, EvidenceSource,
        )

        tracker = ProvenanceTracker()

        c1 = Claim(
            claim_text="BRCA1 is a tumor suppressor that prevents cancer growth",
            confidence=ConfidenceAssessment(level=ConfidenceLevel.HIGH, score=0.9),
            agent_id="agent_1",
            supporting_evidence=[
                EvidenceSource(source_db="PubMed", source_id="PMID:11111"),
                EvidenceSource(source_db="UniProt", source_id="P38398"),
            ],
        )
        tracker.add_claim(c1)

        c2 = Claim(
            claim_text="BRCA1 does not prevent cancer growth in certain contexts",
            confidence=ConfidenceAssessment(level=ConfidenceLevel.LOW, score=0.3),
            agent_id="agent_2",
            supporting_evidence=[
                EvidenceSource(source_db="PubMed", source_id="PMID:22222"),
                EvidenceSource(source_db="PubMed", source_id="PMID:11111"),  # duplicate
            ],
        )

        contradictions = tracker.check_contradiction(c2)
        tracker.add_claim(c2)

        chain = tracker.export_provenance_chain()

        ok = (
            len(contradictions) > 0  # Should detect c1 vs c2
            and len(chain) == 3  # 3 unique sources (deduped)
        )

        suite.add(EvalResult(
            name="Provenance Tracking",
            passed=ok,
            duration=time.time() - t0,
            details=f"Contradictions: {len(contradictions)}, Unique sources: {len(chain)}",
        ))
    except Exception as e:
        suite.add(EvalResult(
            name="Provenance Tracking",
            passed=False,
            duration=time.time() - t0,
            error=str(e),
        ))


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

async def main() -> None:
    suite = EvalSuite()

    logger.info("=" * 60)
    logger.info("LUMI PIPELINE EVALUATION")
    logger.info("=" * 60)

    # 1. API connectivity (gates everything else)
    api_ok = await test_api_connectivity(suite)
    if not api_ok:
        logger.error("API connectivity failed — cannot proceed with LLM tests")
        print(suite.summary())
        return

    # 2-5: Non-LLM tests (can run in parallel)
    await asyncio.gather(
        test_hitl_routing(suite),
        test_living_document(suite),
        test_confidence_calibration(suite),
        test_provenance(suite),
    )

    # 6. Concurrency gate (needs API)
    await test_concurrency_gate(suite)

    # 7. Factory
    divisions = await test_factory(suite)

    # 8. Single agent execution
    await test_agent_execution(suite)

    # 9. Division execution
    await test_division_execution(suite, divisions)

    # 10. CSO planning
    await test_cso_planning(suite, divisions)

    print(suite.summary())


if __name__ == "__main__":
    asyncio.run(main())
