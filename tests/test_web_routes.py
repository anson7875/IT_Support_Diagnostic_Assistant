"""Automated tests for the bilingual Flask web application routes and API."""

from __future__ import annotations

from pathlib import Path

from app import create_app


def _make_client(tmp_path: Path):
    app = create_app(db_path=tmp_path / "web_test.db", testing=True)
    return app.test_client()


def test_homepage_and_language_toggle(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    # Default Traditional Chinese UI
    res_zh = client.get("/")
    assert res_zh.status_code == 200
    assert "IT 支援診斷與案件管理系統" in res_zh.get_data(as_text=True)

    # Switch to English
    res_en = client.get("/set-lang/en", follow_redirects=True)
    assert res_en.status_code == 200
    assert "IT Support Diagnostic &amp; Case Management" in res_en.get_data(as_text=True)


def test_end_to_end_web_flow_and_report_exports(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    # 1. Create incident -> redirects to active session
    res_create = client.post(
        "/incidents/create",
        data={
            "description": "My MacBook is connected to Wi-Fi but has no internet",
            "target_os": "macos",
        },
        follow_redirects=False,
    )
    assert res_create.status_code == 302
    session_url = res_create.headers["Location"]
    assert "/session/SES-" in session_url

    # 2. View Step 1 -> shows macOS command & Cross-OS Learning Panel
    res_step1 = client.get(session_url)
    html1 = res_step1.get_data(as_text=True)
    assert res_step1.status_code == 200
    assert "NET-001-S1" in html1
    assert "networksetup -listallhardwareports" in html1
    assert "WINDOWS" in html1 and "LINUX" in html1 and "MACOS" in html1

    # 3. Submit Step 1 -> advances to Step 2 (IP config with parser)
    res_sub1 = client.post(
        f"{session_url}/submit",
        data={"selection": "outcome:link_connected"},
        follow_redirects=True,
    )
    assert "NET-001-S2" in res_sub1.get_data(as_text=True)

    # 4. Call JSON parser API directly
    api_res = client.post(
        "/api/parse-output",
        json={
            "parser_key": "ip_config",
            "target_os": "macos",
            "raw_output": "inet 169.254.42.18 netmask 0xffff0000\nstatus: active",
        },
    )
    assert api_res.status_code == 200
    payload = api_res.get_json()
    assert payload["suggested_outcome_id"] == "apipa_or_no_ip"

    # 5. Submit Step 2 with raw command output -> Step 2B -> Escalate -> Report
    client.post(
        f"{session_url}/submit",
        data={"raw_command_output": "inet 169.254.42.18 netmask 0xffff0000\nstatus: active"},
        follow_redirects=True,
    )
    res_final = client.post(
        f"{session_url}/submit",
        data={"selection": "outcome:dhcp_renewal_failed"},
        follow_redirects=False,
    )
    assert res_final.status_code == 302
    report_url = res_final.headers["Location"]
    assert "/report" in report_url

    # 6. Verify Report page, Printable HTML, and Markdown download
    res_report = client.get(report_url)
    assert res_report.status_code == 200
    assert "169.254.42.18" in res_report.get_data(as_text=True)

    res_print = client.get(f"{report_url}/print")
    assert res_print.status_code == 200
    assert "<!DOCTYPE html>" in res_print.get_data(as_text=True)

    res_md = client.get(f"{report_url}/markdown")
    assert res_md.status_code == 200
    assert "# IT Incident" in res_md.get_data(as_text=True)


def test_ambiguous_incident_prompts_workflow_selection(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    res = client.post(
        "/incidents/create",
        data={"description": "wifi slow", "target_os": "windows"},
    )
    assert res.status_code == 200
    assert "NET-001" in res.get_data(as_text=True)
    assert "OS-001" in res.get_data(as_text=True)
