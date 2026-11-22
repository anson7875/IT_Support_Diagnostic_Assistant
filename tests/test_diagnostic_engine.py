"""Unit tests for the deterministic Diagnostic Engine."""

from __future__ import annotations

import pytest

from app.diagnostic.diagnostic_engine import (
    DiagnosticEngine,
    DiagnosticEngineError,
)
from app.knowledge.knowledge_base import KnowledgeBase


def _make_engine() -> DiagnosticEngine:
    kb = KnowledgeBase()
    kb.load_all()
    return DiagnosticEngine(kb)


def test_start_session_and_resolve_cross_os_step() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-001", "NET-001", target_os="macos")

    assert session.status == "active"
    assert session.current_step_id == "NET-001-S1"

    step = engine.get_current_step(session)
    assert step is not None
    assert step["resolved_os"] == "macos"
    assert step["active_command"] == "networksetup -listallhardwareports"
    assert len(step["references"]) == 1


def test_network_workflow_with_command_output_parsing_to_escalation() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-002", "NET-001", target_os="macos")

    # Step 1: Link connected -> S2
    res1 = engine.submit_step_result(session, outcome_id="link_connected")
    assert res1["action"] == "next_step"
    assert res1["next_step_id"] == "NET-001-S2"
    assert "Airplane Mode enabled" in session.ruled_out_causes

    # Step 2: Paste macOS ifconfig APIPA output -> auto-routes to S2B (Renew DHCP)
    apipa_output = """
    en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        inet 169.254.42.18 netmask 0xffff0000 broadcast 169.254.255.255
        status: active
    """
    res2 = engine.submit_step_result(session, raw_command_output=apipa_output)
    assert res2["parsed_output"]["suggested_outcome_id"] == "apipa_or_no_ip"
    assert res2["next_step_id"] == "NET-001-S2B"
    assert any(ev.source == "output_parser" for ev in session.evidence)

    # Step 2B: DHCP renewal fails -> Escalate
    res3 = engine.submit_step_result(session, outcome_id="dhcp_renewal_failed")
    assert res3["status"] == "escalated"
    assert session.current_step_id is None
    assert session.escalation_reason is not None
    # Findings are evidence_supported, NEVER auto-confirmed
    assert all(f.status != "confirmed" for f in session.findings)
    assert any(f.status == "evidence_supported" for f in session.findings)


def test_network_workflow_ping_parser_happy_path_to_dns() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-003", "NET-001", target_os="linux")

    engine.submit_step_result(session, outcome_id="link_connected")
    engine.submit_step_result(session, outcome_id="valid_ip_and_gateway")

    # Step 3: Paste Linux ping success -> S4
    ping_ok = """
    4 packets transmitted, 4 received, 0% packet loss, time 3005ms
    rtt min/avg/max/mdev = 1.1/2.2/3.3/0.4 ms
    """
    res3 = engine.submit_step_result(session, raw_command_output=ping_ok)
    assert res3["next_step_id"] == "NET-001-S4"

    # Step 4: Paste Linux ping success to 8.8.8.8 -> S5 (DNS)
    res4 = engine.submit_step_result(session, raw_command_output=ping_ok)
    assert res4["next_step_id"] == "NET-001-S5"

    # Step 5: DNS resolves -> Complete
    res5 = engine.submit_step_result(session, outcome_id="dns_succeeded")
    assert res5["status"] == "completed"
    assert session.current_step_id is None


def test_safety_stop_overrides_normal_submission() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-004", "HW-001", target_os="windows")

    # Even if user passes a normal outcome_id, safety_flag_id MUST override it!
    res = engine.submit_step_result(
        session,
        outcome_id="external_power_verified",
        safety_flag_id="HW-RF-02",
        user_notes="Laptop bottom case is visibly bulging",
    )
    assert res["status"] == "safety_stop"
    assert res["action"] == "safety_stop"
    assert session.current_step_id is None
    assert session.safety_alert is not None
    assert session.safety_alert["flag_id"] == "HW-RF-02"
    assert engine.get_current_step(session) is None


def test_max_visits_prevents_infinite_loop_on_repeated_inconclusive() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-005", "OS-001", target_os="windows")

    # OS-001-S1 has max_visits = 2
    res1 = engine.submit_step_result(session, result_code="inconclusive")
    assert res1["status"] == "active"
    assert res1["action"] == "request_more_information"

    res2 = engine.submit_step_result(session, result_code="inconclusive")
    assert res2["status"] == "paused"
    assert res2["action"] == "pause"
    assert "Maximum visit limit" in res2["summary"]


def test_evidence_is_appended_not_overwritten_on_repeat() -> None:
    engine = _make_engine()
    session = engine.start_session("INC-006", "OS-001", target_os="linux")

    engine.submit_step_result(session, result_code="inconclusive", user_notes="First try")
    engine.submit_step_result(session, outcome_id="cpu_saturated", user_notes="Second try")

    step1_evidence = [e for e in session.evidence if e.step_id == "OS-001-S1"]
    assert len(step1_evidence) == 2
    assert session.current_step_id == "OS-001-S2A"


def test_invalid_inputs_raise_engine_errors() -> None:
    engine = _make_engine()

    with pytest.raises(DiagnosticEngineError, match="Unsupported target_os"):
        engine.start_session("INC-X", "NET-001", target_os="solaris")

    with pytest.raises(DiagnosticEngineError, match="not found"):
        engine.start_session("INC-X", "UNKNOWN-999", target_os="windows")

    session = engine.start_session("INC-007", "HW-001", target_os="windows")
    with pytest.raises(DiagnosticEngineError, match="Invalid outcome_id"):
        engine.submit_step_result(session, outcome_id="nonexistent_outcome")

    with pytest.raises(DiagnosticEngineError, match="Unknown safety red flag"):
        engine.trigger_safety_stop(session, flag_id="FAKE-FLAG")
