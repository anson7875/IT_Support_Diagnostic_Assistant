"""Integration tests for SQLite incident persistence and handoff report generation."""

from __future__ import annotations

from pathlib import Path

from app.database.db import Database
from app.knowledge.knowledge_base import KnowledgeBase
from app.services.incident_service import IncidentService
from app.services.report_service import (
    build_report_data,
    render_markdown_report,
    render_printable_html_report,
)


def _build_service(tmp_path: Path) -> IncidentService:
    db = Database(tmp_path / "test_incidents.db")
    db.init_db()
    kb = KnowledgeBase()
    kb.load_all()
    return IncidentService(db, kb)


def test_full_persisted_network_escalation_and_reports(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    created = service.create_incident(
        description="My MacBook is connected to Wi-Fi but has no internet",
        target_os="macos",
    )
    incident_id = created["incident"]["incident_id"]
    session_id = created["session"]["session_id"]

    assert created["incident"]["workflow_id"] == "NET-001"
    assert created["incident"]["target_os"] == "macos"

    # Step 1: Link connected
    service.submit_step(session_id, outcome_id="link_connected")

    # Step 2: Paste macOS APIPA output -> auto-routes to S2B
    apipa_snippet = """
    en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        inet 169.254.42.18 netmask 0xffff0000 broadcast 169.254.255.255
        status: active
    """
    res2 = service.submit_step(session_id, raw_command_output=apipa_snippet)
    assert res2["next_step_id"] == "NET-001-S2B"

    # Step 2B: DHCP renewal failed -> escalated
    res3 = service.submit_step(
        session_id,
        outcome_id="dhcp_renewal_failed",
        user_notes="Still 169.254.42.18 after Renew DHCP Lease",
    )
    assert res3["status"] == "escalated"

    # Re-instantiate a fresh service pointing at the same SQLite DB to verify persistence
    fresh_service = _build_service(tmp_path)
    reloaded_incident = fresh_service.get_incident(incident_id)
    assert reloaded_incident is not None
    assert reloaded_incident["status"] == "escalated"

    report_data = build_report_data(fresh_service, incident_id)
    assert "Unconfirmed" in report_data["root_cause_status"]

    md = render_markdown_report(report_data)
    assert incident_id in md
    assert "Airplane Mode enabled" in md  # Ruled-out cause
    assert "169.254.42.18" in md  # Parsed APIPA evidence
    assert "EVIDENCE_SUPPORTED" in md

    html_doc = render_printable_html_report(report_data)
    assert "<html" in html_doc
    assert incident_id in html_doc
    assert "Ruled-Out Causes" in html_doc


def test_safety_stop_persisted_and_highlighted_in_report(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    created = service.create_incident(
        description="Desktop PC won't power on",
        target_os="windows",
    )
    incident_id = created["incident"]["incident_id"]
    session_id = created["session"]["session_id"]

    res = service.submit_step(
        session_id,
        safety_flag_id="HW-RF-01",
        user_notes="Faint burning smell near rear PSU",
    )
    assert res["status"] == "safety_stop"

    inc = service.get_incident(incident_id)
    assert inc is not None
    assert inc["status"] == "safety_stop"

    report_data = build_report_data(service, incident_id)
    md = render_markdown_report(report_data)
    html_doc = render_printable_html_report(report_data)
    assert "SAFETY STOP ALERT" in md
    assert "HW-RF-01" in html_doc


def test_technician_resolution_and_explicit_root_cause_confirmation(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    created = service.create_incident(
        description="Ubuntu Linux machine is very slow with high CPU usage",
        target_os="linux",
    )
    incident_id = created["incident"]["incident_id"]
    session_id = created["session"]["session_id"]

    service.submit_step(session_id, outcome_id="cpu_saturated")
    service.submit_step(session_id, outcome_id="runaway_user_app")

    findings = service.get_findings(incident_id)
    assert len(findings) >= 1
    assert all(f["status"] == "evidence_supported" for f in findings)

    # Explicitly confirm the last finding and record resolution notes
    service.record_resolution(
        incident_id,
        resolution_notes="Restarted runaway browser process; CPU dropped to 8%.",
        confirm_finding_id=findings[-1]["id"],
    )

    report_data = build_report_data(service, incident_id)
    assert report_data["root_cause_status"].startswith("Confirmed")
    md = render_markdown_report(report_data)
    assert "CONFIRMED" in md
    assert "Restarted runaway browser process" in md
