"""Rule-based IT incident classifier.

Classifies natural-language incident descriptions into supported categories
(``hardware``, ``os``, ``network``) and recommends a matching flagship
workflow without forcing guesses on ambiguous or unsupported incidents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.diagnostic.keyword_extractor import (
    ExtractedIncidentInfo,
    extract_incident_info,
)

CATEGORY_TO_DEFAULT_WORKFLOW: dict[str, str] = {
    "hardware": "HW-001",
    "os": "OS-001",
    "network": "NET-001",
}


@dataclass(frozen=True)
class ClassificationResult:
    """Deterministic classification output for an IT incident."""

    category: str | None
    recommended_workflow_id: str | None
    confidence: str  # high | medium | ambiguous | unsupported
    scores: dict[str, int]
    extracted_info: ExtractedIncidentInfo
    missing_information: list[str] = field(default_factory=list)
    safety_warning: str | None = None
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the classification result into a plain dictionary."""
        return asdict(self)


def classify_incident(
    description: str, target_os: str | None = None
) -> ClassificationResult:
    """Classify an incident description into a supported category and workflow.

    Avoids forcing a category when symptoms are empty, unsupported, or tied
    between multiple categories.
    """
    extracted = extract_incident_info(description)
    scores = {cat: len(hits) for cat, hits in extracted.matched_keywords.items()}

    safety_warning: str | None = None
    if extracted.safety_keywords_detected:
        safety_warning = (
            "SAFETY ALERT: Potential physical/electrical hazard keywords detected "
            f"({', '.join(extracted.safety_keywords_detected)}). "
            "Stop normal troubleshooting immediately and follow safety escalation procedures."
        )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_category, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    missing_info: list[str] = []
    effective_os = (target_os or "").strip().lower() or extracted.detected_os

    if top_score == 0:
        return ClassificationResult(
            category=None,
            recommended_workflow_id=None,
            confidence="unsupported",
            scores=scores,
            extracted_info=extracted,
            missing_information=["symptom_details"] + (["target_os"] if not effective_os else []),
            safety_warning=safety_warning,
            explanation=(
                "No supported Hardware, Operating System, or Networking keywords were "
                "matched. Please provide more symptom details or select a workflow manually."
            ),
        )

    if top_score == second_score:
        tied = [cat for cat, sc in ranked if sc == top_score]
        return ClassificationResult(
            category=None,
            recommended_workflow_id=None,
            confidence="ambiguous",
            scores=scores,
            extracted_info=extracted,
            missing_information=["clarify_primary_symptom"]
            + (["target_os"] if not effective_os else []),
            safety_warning=safety_warning,
            explanation=(
                f"Incident description matches multiple categories equally ({', '.join(tied)}). "
                "Please clarify the primary symptom or select the intended workflow."
            ),
        )

    confidence = "high" if (top_score >= 2 or (top_score - second_score) >= 2) else "medium"
    if top_category in {"os", "network"} and not effective_os:
        missing_info.append("target_os")

    workflow_id = CATEGORY_TO_DEFAULT_WORKFLOW[top_category]
    matched_list = ", ".join(extracted.matched_keywords[top_category])

    return ClassificationResult(
        category=top_category,
        recommended_workflow_id=workflow_id,
        confidence=confidence,
        scores=scores,
        extracted_info=extracted,
        missing_information=missing_info,
        safety_warning=safety_warning,
        explanation=(
            f"Classified as '{top_category}' ({confidence} confidence) based on "
            f"matched signals: {matched_list}. Recommended workflow: {workflow_id}."
        ),
    )
