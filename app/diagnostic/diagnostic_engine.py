"""Deterministic Diagnostic Workflow Engine.

Controls diagnostic session state, cross-OS step presentation, multi-outcome
and fallback transition evaluation, evidence recording, ruled-out cause
tracking, cycle/visit-limit protection, and safety-stop overrides.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.diagnostic.output_parser import ParsedCommandResult, parse_command_output
from app.knowledge.knowledge_base import CONCRETE_OS_VALUES, KnowledgeBase


class DiagnosticEngineError(ValueError):
    """Raised when an invalid operation or input is submitted to the engine."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvidenceRecord:
    """Traceable piece of evidence recorded during a diagnostic step."""

    step_id: str
    evidence_type: str
    description: str
    raw_value: Any
    recorded_at: str = field(default_factory=_utc_now_iso)
    source: str = "user"


@dataclass
class StepExecutionRecord:
    """Immutable audit record of a single diagnostic step evaluation."""

    step_id: str
    step_title: str
    result_code: str
    outcome_id: str | None
    action_taken: str
    summary: str
    user_notes: str = ""
    recorded_at: str = field(default_factory=_utc_now_iso)


@dataclass
class FindingRecord:
    """Diagnostic finding backed by recorded observations (never auto-confirmed)."""

    description: str
    status: str  # possible | suspected | evidence_supported | confirmed
    step_id: str


@dataclass
class DiagnosticSession:
    """Stateful representation of a single diagnostic workflow execution."""

    session_id: str
    incident_id: str
    workflow_id: str
    target_os: str
    current_step_id: str | None
    status: str = "active"  # active | paused | completed | escalated | safety_stop
    visit_counts: dict[str, int] = field(default_factory=dict)
    history: list[StepExecutionRecord] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    ruled_out_causes: list[str] = field(default_factory=list)
    findings: list[FindingRecord] = field(default_factory=list)
    safety_alert: dict[str, Any] | None = None
    escalation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the session state into a plain JSON-compatible dict."""
        return asdict(self)


class DiagnosticEngine:
    """Data-driven, deterministic diagnostic workflow execution engine."""

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.kb = knowledge_base

    def start_session(
        self,
        incident_id: str,
        workflow_id: str,
        target_os: str = "windows",
        session_id: str | None = None,
    ) -> DiagnosticSession:
        """Initialize a new diagnostic session for the given workflow and target OS."""
        os_key = target_os.lower()
        if os_key not in CONCRETE_OS_VALUES:
            raise DiagnosticEngineError(
                f"Unsupported target_os '{target_os}'. Choose from {sorted(CONCRETE_OS_VALUES)}."
            )

        try:
            workflow = self.kb.get_workflow(workflow_id)
        except KeyError as exc:
            raise DiagnosticEngineError(str(exc)) from exc

        supported_os = workflow["supported_os"]
        if "all" not in supported_os and os_key not in supported_os:
            raise DiagnosticEngineError(
                f"Workflow '{workflow_id}' does not support target_os '{os_key}'."
            )

        return DiagnosticSession(
            session_id=session_id or f"SES-{uuid.uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            workflow_id=workflow_id,
            target_os=os_key,
            current_step_id=workflow["initial_step_id"],
            status="active",
        )

    def get_current_step(
        self, session: DiagnosticSession, lang: str = "en"
    ) -> dict[str, Any] | None:
        """Return the current OS-resolved diagnostic step, or None if session is not active."""
        if session.status != "active" or session.current_step_id is None:
            return None

        workflow = self.kb.get_workflow(session.workflow_id, lang=lang)
        step = self.kb.resolve_step_for_os(
            session.workflow_id, session.current_step_id, session.target_os, lang=lang
        )
        step["references"] = self.kb.get_references_for_step(
            session.workflow_id, session.current_step_id
        )
        step["workflow_safety_red_flags"] = list(workflow.get("safety_red_flags", []))
        return step

    def _find_safety_flag(
        self, workflow: dict[str, Any], step: dict[str, Any] | None, flag_id: str
    ) -> dict[str, Any] | None:
        for flag in workflow.get("safety_red_flags", []):
            if flag["flag_id"] == flag_id:
                return flag
        if step:
            for flag in step.get("safety_red_flags", []):
                if flag["flag_id"] == flag_id:
                    return flag
        return None

    def trigger_safety_stop(
        self,
        session: DiagnosticSession,
        flag_id: str,
        user_notes: str = "",
    ) -> dict[str, Any]:
        """Immediately halt the workflow due to a safety red flag override."""
        if session.status in {"completed", "escalated", "safety_stop"}:
            raise DiagnosticEngineError(
                f"Cannot trigger safety_stop on terminated session (status='{session.status}')."
            )

        workflow = self.kb.get_workflow(session.workflow_id)
        current_step = (
            self.kb.get_step(session.workflow_id, session.current_step_id)
            if session.current_step_id
            else None
        )
        flag = self._find_safety_flag(workflow, current_step, flag_id)
        if flag is None:
            raise DiagnosticEngineError(
                f"Unknown safety red flag '{flag_id}' for workflow '{session.workflow_id}'."
            )

        step_id = session.current_step_id or workflow["initial_step_id"]
        step_title = current_step["title"] if current_step else "Safety Override"

        session.evidence.append(
            EvidenceRecord(
                step_id=step_id,
                evidence_type="user_report",
                description=f"Safety red flag reported: {flag['label']}",
                raw_value={"flag_id": flag_id, "user_notes": user_notes},
                source="user",
            )
        )
        session.history.append(
            StepExecutionRecord(
                step_id=step_id,
                step_title=step_title,
                result_code="abnormal",
                outcome_id=None,
                action_taken="safety_stop",
                summary=flag["warning_message"],
                user_notes=user_notes,
            )
        )
        session.status = "safety_stop"
        session.current_step_id = None
        session.safety_alert = dict(flag)
        session.escalation_reason = flag["escalation_instruction"]

        return {
            "status": session.status,
            "action": "safety_stop",
            "summary": flag["warning_message"],
            "next_step_id": None,
            "parsed_output": None,
            "safety_alert": session.safety_alert,
        }

    def submit_step_result(
        self,
        session: DiagnosticSession,
        outcome_id: str | None = None,
        result_code: str | None = None,
        raw_command_output: str | None = None,
        user_notes: str = "",
        safety_flag_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a submitted step result and advance the session deterministically.

        Safety flags take absolute priority over ordinary result transitions.
        """
        if session.status != "active" or session.current_step_id is None:
            raise DiagnosticEngineError(
                f"Cannot submit step result when session status is '{session.status}'."
            )

        # Safety override always takes priority over normal branching
        if safety_flag_id:
            return self.trigger_safety_stop(
                session, flag_id=safety_flag_id, user_notes=user_notes
            )

        step_id = session.current_step_id
        step = self.kb.get_step(session.workflow_id, step_id)

        # Optional deterministic command output parsing
        parsed_result: ParsedCommandResult | None = None
        if raw_command_output and raw_command_output.strip():
            session.evidence.append(
                EvidenceRecord(
                    step_id=step_id,
                    evidence_type="command_output",
                    description=f"Raw command output submitted for {step['title']}",
                    raw_value=raw_command_output.strip(),
                    source="user",
                )
            )
            parser_key = step.get("parser_key")
            if parser_key:
                parsed_result = parse_command_output(
                    parser_key, raw_command_output, target_os=session.target_os
                )
                session.evidence.append(
                    EvidenceRecord(
                        step_id=step_id,
                        evidence_type="measurement",
                        description=parsed_result.summary,
                        raw_value=parsed_result.extracted_metrics,
                        source="output_parser",
                    )
                )
                if outcome_id is None and result_code is None:
                    outcome_id = parsed_result.suggested_outcome_id
                    if outcome_id is None:
                        result_code = parsed_result.suggested_result_code

        # Resolve outcome or fallback result transition
        selected_outcome: dict[str, Any] | None = None
        if outcome_id is not None:
            for candidate in step["outcomes"]:
                if candidate["outcome_id"] == outcome_id:
                    selected_outcome = candidate
                    break
            if selected_outcome is None:
                raise DiagnosticEngineError(
                    f"Invalid outcome_id '{outcome_id}' for step '{step_id}'."
                )
            resolved_result_code = selected_outcome["result_code"]
            transition = selected_outcome["transition"]
        elif result_code is not None:
            # If the caller supplied only a result_code (e.g., from ping parser),
            # match a unique outcome with that result_code when available,
            # otherwise fall back to result_transitions.
            matching_outcomes = [
                o for o in step["outcomes"] if o["result_code"] == result_code
            ]
            if len(matching_outcomes) == 1:
                selected_outcome = matching_outcomes[0]
                outcome_id = selected_outcome["outcome_id"]
                resolved_result_code = result_code
                transition = selected_outcome["transition"]
            elif result_code in step["result_transitions"]:
                resolved_result_code = result_code
                transition = step["result_transitions"][result_code]
            else:
                # Safe missing-transition policy: pause without guessing
                return self._pause_for_missing_transition(
                    session, step, result_code, user_notes, parsed_result
                )
        else:
            raise DiagnosticEngineError(
                "Either outcome_id, result_code, or raw_command_output must be provided."
            )

        # Record visit count for cycle control
        session.visit_counts[step_id] = session.visit_counts.get(step_id, 0) + 1

        # Record test result evidence (append-only, never overwrite)
        evidence_desc = (
            selected_outcome["label"]
            if selected_outcome
            else f"Recorded result '{resolved_result_code}' for {step['title']}"
        )
        session.evidence.append(
            EvidenceRecord(
                step_id=step_id,
                evidence_type="test_result",
                description=evidence_desc,
                raw_value={
                    "result_code": resolved_result_code,
                    "outcome_id": outcome_id,
                    "user_notes": user_notes,
                },
                source="user",
            )
        )

        # Record ruled-out causes & evidence-supported findings (never auto-confirmed)
        if selected_outcome:
            for ruled_out in selected_outcome.get("rules_out", []):
                if ruled_out not in session.ruled_out_causes:
                    session.ruled_out_causes.append(ruled_out)
            finding_hint = selected_outcome.get("finding_hint")
            if finding_hint:
                session.findings.append(
                    FindingRecord(
                        description=finding_hint,
                        status="evidence_supported",
                        step_id=step_id,
                    )
                )

        action = transition["action"]
        next_step_id = transition.get("next_step_id")
        summary = transition.get("summary") or f"Action '{action}' applied."

        # Apply transition & enforce max_visits cycle protection
        if action == "next_step":
            next_step = self.kb.get_step(session.workflow_id, next_step_id)
            if session.visit_counts.get(next_step_id, 0) >= next_step["max_visits"]:
                action = "pause"
                summary = (
                    f"Maximum visit limit ({next_step['max_visits']}) reached for step "
                    f"'{next_step_id}'. Workflow paused safely to prevent an infinite loop."
                )
                session.status = "paused"
            else:
                session.current_step_id = next_step_id
                session.status = "active"
        elif action == "request_more_information":
            if session.visit_counts[step_id] >= step["max_visits"]:
                action = "pause"
                summary = (
                    f"Maximum visit limit ({step['max_visits']}) reached for step "
                    f"'{step_id}'. Workflow paused safely."
                )
                session.status = "paused"
            else:
                session.status = "active"
                next_step_id = step_id
        elif action == "pause":
            session.status = "paused"
        elif action == "complete":
            session.status = "completed"
            session.current_step_id = None
        elif action == "escalate":
            session.status = "escalated"
            session.current_step_id = None
            session.escalation_reason = summary

        session.history.append(
            StepExecutionRecord(
                step_id=step_id,
                step_title=step["title"],
                result_code=resolved_result_code,
                outcome_id=outcome_id,
                action_taken=action,
                summary=summary,
                user_notes=user_notes,
            )
        )

        return {
            "status": session.status,
            "action": action,
            "summary": summary,
            "next_step_id": session.current_step_id,
            "parsed_output": parsed_result.to_dict() if parsed_result else None,
            "safety_alert": session.safety_alert,
        }

    def _pause_for_missing_transition(
        self,
        session: DiagnosticSession,
        step: dict[str, Any],
        result_code: str,
        user_notes: str,
        parsed_result: ParsedCommandResult | None,
    ) -> dict[str, Any]:
        summary = (
            f"No unambiguous transition defined for result '{result_code}' on step "
            f"'{step['step_id']}'. Workflow paused safely without guessing."
        )
        session.status = "paused"
        session.history.append(
            StepExecutionRecord(
                step_id=step["step_id"],
                step_title=step["title"],
                result_code=result_code,
                outcome_id=None,
                action_taken="pause",
                summary=summary,
                user_notes=user_notes,
            )
        )
        return {
            "status": session.status,
            "action": "pause",
            "summary": summary,
            "next_step_id": session.current_step_id,
            "parsed_output": parsed_result.to_dict() if parsed_result else None,
            "safety_alert": None,
        }
