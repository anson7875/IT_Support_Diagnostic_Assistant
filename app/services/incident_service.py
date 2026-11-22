"""Incident and diagnostic session management service.

Coordinates issue classification, diagnostic engine execution, and SQLite
persistence so every diagnostic step, observation, evidence record, and
finding is durably stored and traceable.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.database.db import Database
from app.diagnostic.classifier import classify_incident
from app.diagnostic.diagnostic_engine import (
    DiagnosticEngine,
    DiagnosticSession,
    EvidenceRecord,
    FindingRecord,
    StepExecutionRecord,
)
from app.knowledge.knowledge_base import CONCRETE_OS_VALUES, KnowledgeBase

SESSION_TO_INCIDENT_STATUS: dict[str, str] = {
    "active": "in_progress",
    "paused": "paused",
    "completed": "resolved",
    "escalated": "escalated",
    "safety_stop": "safety_stop",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentService:
    """Application service coordinating incidents, sessions, and SQLite storage."""

    def __init__(self, db: Database, kb: KnowledgeBase) -> None:
        self.db = db
        self.kb = kb
        self.engine = DiagnosticEngine(kb)

    def create_incident(
        self,
        description: str,
        target_os: str | None = None,
        workflow_id: str | None = None,
        device_type: str | None = None,
    ) -> dict[str, Any]:
        """Create and persist a new incident, classifying it and starting a session when possible."""
        clean_desc = (description or "").strip()
        if not clean_desc:
            raise ValueError("Incident description must not be empty.")

        classification = classify_incident(clean_desc, target_os=target_os)

        resolved_os = (
            (target_os or "").strip().lower()
            or classification.extracted_info.detected_os
            or "windows"
        )
        if resolved_os not in CONCRETE_OS_VALUES:
            raise ValueError(
                f"Unsupported target_os '{resolved_os}'. Choose from {sorted(CONCRETE_OS_VALUES)}."
            )

        resolved_workflow_id = workflow_id or classification.recommended_workflow_id
        resolved_category = classification.category
        if resolved_workflow_id:
            wf = self.kb.get_workflow(resolved_workflow_id)
            resolved_category = wf["category"]

        resolved_device = (
            (device_type or "").strip()
            or classification.extracted_info.device_type
            or "unknown"
        )

        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        now = _utc_now()
        initial_status = "in_progress" if resolved_workflow_id else "open"

        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO incidents (
                    incident_id, description, device_type, target_os, category,
                    workflow_id, status, safety_warning, resolution_notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    clean_desc,
                    resolved_device,
                    resolved_os,
                    resolved_category,
                    resolved_workflow_id,
                    initial_status,
                    classification.safety_warning,
                    None,
                    now,
                    now,
                ),
            )

        session_dict: dict[str, Any] | None = None
        if resolved_workflow_id:
            session = self.start_session_for_incident(
                incident_id=incident_id,
                workflow_id=resolved_workflow_id,
                target_os=resolved_os,
            )
            session_dict = session.to_dict()

        return {
            "incident": self.get_incident(incident_id),
            "classification": classification.to_dict(),
            "session": session_dict,
        }

    def start_session_for_incident(
        self, incident_id: str, workflow_id: str, target_os: str
    ) -> DiagnosticSession:
        """Start and persist a new diagnostic session attached to an existing incident."""
        incident = self.get_incident(incident_id)
        if incident is None:
            raise KeyError(f"Incident '{incident_id}' not found.")

        session = self.engine.start_session(
            incident_id=incident_id,
            workflow_id=workflow_id,
            target_os=target_os,
        )
        now = _utc_now()
        wf = self.kb.get_workflow(workflow_id)

        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO diagnostic_sessions (
                    session_id, incident_id, workflow_id, target_os,
                    current_step_id, status, visit_counts_json, ruled_out_json,
                    safety_alert_json, escalation_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.incident_id,
                    session.workflow_id,
                    session.target_os,
                    session.current_step_id,
                    session.status,
                    json.dumps(session.visit_counts),
                    json.dumps(session.ruled_out_causes),
                    json.dumps(session.safety_alert) if session.safety_alert else None,
                    session.escalation_reason,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                UPDATE incidents
                SET workflow_id = ?, category = ?, target_os = ?, status = 'in_progress', updated_at = ?
                WHERE incident_id = ?
                """,
                (workflow_id, wf["category"], session.target_os, now, incident_id),
            )
        return session

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        """Fetch an incident record with its latest session ID, or None if not found."""
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
            if row is None:
                return None
            incident = dict(row)
            session_row = conn.execute(
                """
                SELECT session_id, status AS session_status
                FROM diagnostic_sessions
                WHERE incident_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (incident_id,),
            ).fetchone()
            incident["latest_session_id"] = (
                session_row["session_id"] if session_row else None
            )
            incident["latest_session_status"] = (
                session_row["session_status"] if session_row else None
            )
            return incident

    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent incidents ordered newest-first."""
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT i.*,
                       (SELECT s.session_id FROM diagnostic_sessions s
                        WHERE s.incident_id = i.incident_id
                        ORDER BY s.created_at DESC LIMIT 1) AS latest_session_id
                FROM incidents i
                ORDER BY i.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def load_session(self, session_id: str) -> DiagnosticSession:
        """Reconstruct a complete DiagnosticSession (including history, evidence, findings) from SQLite."""
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM diagnostic_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Diagnostic session '{session_id}' not found.")

            step_rows = conn.execute(
                "SELECT * FROM step_results WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
            ev_rows = conn.execute(
                "SELECT * FROM evidence_records WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
            finding_rows = conn.execute(
                "SELECT * FROM findings WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()

        history = [
            StepExecutionRecord(
                step_id=r["step_id"],
                step_title=r["step_title"],
                result_code=r["result_code"],
                outcome_id=r["outcome_id"],
                action_taken=r["action_taken"],
                summary=r["summary"],
                user_notes=r["user_notes"],
                recorded_at=r["recorded_at"],
            )
            for r in step_rows
        ]
        evidence = [
            EvidenceRecord(
                step_id=r["step_id"],
                evidence_type=r["evidence_type"],
                description=r["description"],
                raw_value=json.loads(r["raw_value_json"]),
                recorded_at=r["recorded_at"],
                source=r["source"],
            )
            for r in ev_rows
        ]
        findings = [
            FindingRecord(
                description=r["description"],
                status=r["status"],
                step_id=r["step_id"],
            )
            for r in finding_rows
        ]

        return DiagnosticSession(
            session_id=row["session_id"],
            incident_id=row["incident_id"],
            workflow_id=row["workflow_id"],
            target_os=row["target_os"],
            current_step_id=row["current_step_id"],
            status=row["status"],
            visit_counts=json.loads(row["visit_counts_json"]),
            history=history,
            evidence=evidence,
            ruled_out_causes=json.loads(row["ruled_out_json"]),
            findings=findings,
            safety_alert=(
                json.loads(row["safety_alert_json"])
                if row["safety_alert_json"]
                else None
            ),
            escalation_reason=row["escalation_reason"],
        )

    def get_current_step(
        self, session_id: str, lang: str = "en"
    ) -> dict[str, Any] | None:
        """Return the active OS-resolved step for a persisted session."""
        session = self.load_session(session_id)
        return self.engine.get_current_step(session, lang=lang)

    def submit_step(
        self,
        session_id: str,
        outcome_id: str | None = None,
        result_code: str | None = None,
        raw_command_output: str | None = None,
        user_notes: str = "",
        safety_flag_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a step submission and persist all newly created records atomically."""
        session = self.load_session(session_id)
        prev_history_len = len(session.history)
        prev_evidence_len = len(session.evidence)
        prev_findings_len = len(session.findings)

        outcome = self.engine.submit_step_result(
            session,
            outcome_id=outcome_id,
            result_code=result_code,
            raw_command_output=raw_command_output,
            user_notes=user_notes,
            safety_flag_id=safety_flag_id,
        )

        new_history = session.history[prev_history_len:]
        new_evidence = session.evidence[prev_evidence_len:]
        new_findings = session.findings[prev_findings_len:]
        now = _utc_now()
        incident_status = SESSION_TO_INCIDENT_STATUS.get(session.status, "in_progress")

        with self.db.connect() as conn:
            for rec in new_history:
                conn.execute(
                    """
                    INSERT INTO step_results (
                        session_id, step_id, step_title, result_code, outcome_id,
                        action_taken, summary, user_notes, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.session_id,
                        rec.step_id,
                        rec.step_title,
                        rec.result_code,
                        rec.outcome_id,
                        rec.action_taken,
                        rec.summary,
                        rec.user_notes,
                        rec.recorded_at,
                    ),
                )
            for ev in new_evidence:
                conn.execute(
                    """
                    INSERT INTO evidence_records (
                        incident_id, session_id, step_id, evidence_type,
                        description, raw_value_json, source, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.incident_id,
                        session.session_id,
                        ev.step_id,
                        ev.evidence_type,
                        ev.description,
                        json.dumps(ev.raw_value, ensure_ascii=False),
                        ev.source,
                        ev.recorded_at,
                    ),
                )
            for finding in new_findings:
                conn.execute(
                    """
                    INSERT INTO findings (
                        incident_id, session_id, step_id, description, status, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.incident_id,
                        session.session_id,
                        finding.step_id,
                        finding.description,
                        finding.status,
                        now,
                    ),
                )
            conn.execute(
                """
                UPDATE diagnostic_sessions
                SET current_step_id = ?, status = ?, visit_counts_json = ?,
                    ruled_out_json = ?, safety_alert_json = ?, escalation_reason = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (
                    session.current_step_id,
                    session.status,
                    json.dumps(session.visit_counts),
                    json.dumps(session.ruled_out_causes, ensure_ascii=False),
                    (
                        json.dumps(session.safety_alert, ensure_ascii=False)
                        if session.safety_alert
                        else None
                    ),
                    session.escalation_reason,
                    now,
                    session.session_id,
                ),
            )
            conn.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ?",
                (incident_status, now, session.incident_id),
            )

        return outcome

    def get_findings(self, incident_id: str) -> list[dict[str, Any]]:
        """Return persisted findings (with database IDs) for an incident."""
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM findings WHERE incident_id = ? ORDER BY id ASC",
                (incident_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def record_resolution(
        self,
        incident_id: str,
        resolution_notes: str,
        confirm_finding_id: int | None = None,
    ) -> dict[str, Any]:
        """Record technician resolution notes and optionally confirm a specific finding."""
        incident = self.get_incident(incident_id)
        if incident is None:
            raise KeyError(f"Incident '{incident_id}' not found.")

        now = _utc_now()
        with self.db.connect() as conn:
            if confirm_finding_id is not None:
                updated = conn.execute(
                    """
                    UPDATE findings
                    SET status = 'confirmed'
                    WHERE id = ? AND incident_id = ?
                    """,
                    (confirm_finding_id, incident_id),
                )
                if updated.rowcount == 0:
                    raise KeyError(
                        f"Finding ID {confirm_finding_id} not found for incident '{incident_id}'."
                    )
            conn.execute(
                """
                UPDATE incidents
                SET resolution_notes = ?, updated_at = ?
                WHERE incident_id = ?
                """,
                (resolution_notes.strip(), now, incident_id),
            )
        return self.get_incident(incident_id) or {}
