"""Confidence calibration utilities.

Converts raw evidence lists into calibrated ``ConfidenceAssessment``
objects using convergence analysis and weighted scoring.
"""

from __future__ import annotations

from typing import Any, Optional

from .types import ConfidenceAssessment, ConfidenceLevel


def calibrate_confidence(evidence_list: list[dict[str, Any]]) -> ConfidenceAssessment:
    """Produce a calibrated confidence assessment from a list of evidence dicts.

    Each evidence dict should contain at minimum:
        - ``source`` (str): identifier of the evidence source
        - ``strength`` (float 0-1): how strong the evidence is

    Optional keys:
        - ``convergence`` (float 0-1): how well it converges with other evidence
        - ``independent`` (bool): whether this is an independent source
        - ``methodology_score`` (float 0-1): quality of the methodology
        - ``effect_size`` (float): observed effect magnitude
        - ``p_value`` (float): statistical significance
        - ``caveat`` (str): limitation of this evidence
        - ``alternative`` (str): alternative explanation

    Returns:
        A fully populated ``ConfidenceAssessment``.
    """
    if not evidence_list:
        return ConfidenceAssessment(
            level=ConfidenceLevel.INSUFFICIENT,
            score=0.0,
            evidence_convergence=0.0,
            caveats=["No evidence provided."],
        )

    # Gather metrics across all evidence items
    strengths: list[float] = []
    convergences: list[float] = []
    methodology_scores: list[float] = []
    independent_count = 0
    caveats: list[str] = []
    alternatives: list[str] = []
    p_values: list[float] = []
    effect_sizes: list[float] = []

    for ev in evidence_list:
        strength = float(ev.get("strength", 0.5))
        strengths.append(strength)

        if "convergence" in ev:
            convergences.append(float(ev["convergence"]))

        if ev.get("independent", False):
            independent_count += 1

        if "methodology_score" in ev:
            methodology_scores.append(float(ev["methodology_score"]))

        if "effect_size" in ev:
            effect_sizes.append(float(ev["effect_size"]))

        if "p_value" in ev:
            p_values.append(float(ev["p_value"]))

        if "caveat" in ev and ev["caveat"]:
            caveats.append(str(ev["caveat"]))

        if "alternative" in ev and ev["alternative"]:
            alternatives.append(str(ev["alternative"]))

    # Weighted average score
    score = _weighted_mean(strengths)

    # Evidence convergence
    evidence_convergence: Optional[float] = None
    if convergences:
        evidence_convergence = _weighted_mean(convergences)

    # Methodology robustness
    methodology_robustness: Optional[float] = None
    if methodology_scores:
        methodology_robustness = _weighted_mean(methodology_scores)

    # Statistical significance (use the minimum p-value = strongest signal)
    stat_sig: Optional[float] = None
    if p_values:
        stat_sig = min(p_values)

    # Effect size (use the maximum)
    effect_size: Optional[float] = None
    if effect_sizes:
        effect_size = max(effect_sizes)

    # Determine discrete confidence level
    level = _determine_level(
        n_sources=len(evidence_list),
        independent_count=independent_count,
        score=score,
        convergence=evidence_convergence,
    )

    return ConfidenceAssessment(
        level=level,
        score=round(score, 4),
        evidence_convergence=round(evidence_convergence, 4) if evidence_convergence is not None else None,
        statistical_significance=stat_sig,
        effect_size=effect_size,
        methodology_robustness=round(methodology_robustness, 4) if methodology_robustness is not None else None,
        independent_replication=independent_count if independent_count > 0 else None,
        caveats=caveats,
        alternative_explanations=alternatives,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _weighted_mean(values: list[float]) -> float:
    """Simple arithmetic mean, clamped to [0, 1]."""
    if not values:
        return 0.0
    return max(0.0, min(1.0, sum(values) / len(values)))


def _determine_level(
    n_sources: int,
    independent_count: int,
    score: float,
    convergence: Optional[float],
) -> ConfidenceLevel:
    """Map quantitative evidence metrics to a discrete confidence level.

    Rules:
        - HIGH: 3+ independent sources agree (convergence >= 0.7 or score >= 0.75)
        - MEDIUM: 1-2 strong sources (score >= 0.5)
        - LOW: suggestive evidence only (score >= 0.2)
        - INSUFFICIENT: no meaningful evidence (score < 0.2 or no sources)
    """
    if n_sources == 0:
        return ConfidenceLevel.INSUFFICIENT

    has_strong_convergence = convergence is not None and convergence >= 0.7

    if independent_count >= 3 and (has_strong_convergence or score >= 0.75):
        return ConfidenceLevel.HIGH

    if score >= 0.5 and n_sources >= 1:
        return ConfidenceLevel.MEDIUM

    if score >= 0.2:
        return ConfidenceLevel.LOW

    return ConfidenceLevel.INSUFFICIENT
