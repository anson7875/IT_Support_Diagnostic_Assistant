"""Incident and L1-to-L2 Escalation Handoff Report generator.

Builds structured report payloads from persisted incident/session records and
renders clean, handoff-ready Markdown and printable HTML reports while
strictly distinguishing evidence-supported findings from confirmed root causes.
"""

from __future__ import annotations

import html
from typing import Any

from app.services.incident_service import IncidentService


def build_report_data(service: IncidentService, incident_id: str) -> dict[str, Any]:
    """Assemble all traceable incident, session, evidence, and finding data for reporting."""
    incident = service.get_incident(incident_id)
    if incident is None:
        raise KeyError(f"Incident '{incident_id}' not found.")

    session_data: dict[str, Any] | None = None
    workflow_name: str | None = None
    if incident.get("latest_session_id"):
        session = service.load_session(incident["latest_session_id"])
        session_data = session.to_dict()
        try:
            workflow_name = service.kb.get_workflow(session.workflow_id)["workflow_name"]
        except KeyError:
            workflow_name = session.workflow_id

    findings = service.get_findings(incident_id)
    confirmed_findings = [f for f in findings if f["status"] == "confirmed"]
    unconfirmed_findings = [f for f in findings if f["status"] != "confirmed"]

    root_cause_status = (
        "Confirmed (verified by technician)"
        if confirmed_findings
        else "Unconfirmed (evidence-supported findings only; further L2 verification recommended)"
        if unconfirmed_findings
        else "Undetermined (insufficient diagnostic evidence)"
    )

    recommendations: list[str] = []
    if session_data:
        if session_data.get("safety_alert"):
            recommendations.append(
                f"SAFETY PRIORITY: {session_data['safety_alert']['escalation_instruction']}"
            )
        if session_data.get("escalation_reason"):
            recommendations.append(session_data["escalation_reason"])
    if not recommendations:
        if incident["status"] == "resolved":
            recommendations.append(
                "Verify stability with the end user and document any configuration changes."
            )
        else:
            recommendations.append(
                "Continue structured diagnostic workflow or escalate with attached evidence."
            )

    return {
        "incident": incident,
        "workflow_name": workflow_name,
        "session": session_data,
        "findings": findings,
        "root_cause_status": root_cause_status,
        "recommendations": recommendations,
    }


def render_markdown_report(report_data: dict[str, Any]) -> str:
    """Render a handoff-ready Markdown report suitable for L1-to-L2 ticket escalation."""
    inc = report_data["incident"]
    session = report_data.get("session")
    findings = report_data.get("findings", [])

    lines: list[str] = [
        f"# IT Incident & Escalation Handoff Report (`{inc['incident_id']}`)",
        "",
        "## 1. Incident Summary",
        f"- **Incident ID:** `{inc['incident_id']}`",
        f"- **Status:** `{inc['status']}`",
        f"- **Target OS:** `{inc['target_os']}`",
        f"- **Device Type:** `{inc.get('device_type') or 'unknown'}`",
        f"- **Category:** `{inc.get('category') or 'unclassified'}`",
        f"- **Workflow:** `{inc.get('workflow_id') or 'N/A'}` ({report_data.get('workflow_name') or 'Not started'})",
        f"- **Created At (UTC):** {inc['created_at']}",
        "",
        "## 2. Reported Symptoms",
        inc["description"],
        "",
    ]

    if session and session.get("safety_alert"):
        alert = session["safety_alert"]
        lines.extend(
            [
                "## SAFETY STOP ALERT",
                f"- **Trigger:** {alert['label']} (`{alert['flag_id']}`)",
                f"- **Warning:** {alert['warning_message']}",
                f"- **Required Action:** {alert['escalation_instruction']}",
                "",
            ]
        )

    lines.append("## 3. Diagnostic Steps Performed")
    if session and session.get("history"):
        for idx, step in enumerate(session["history"], start=1):
            notes_part = f" | Notes: {step['user_notes']}" if step.get("user_notes") else ""
            lines.append(
                f"{idx}. **{step['step_id']} — {step['step_title']}** "
                f"(`{step['result_code']}` -> `{step['action_taken']}`): {step['summary']}{notes_part}"
            )
    else:
        lines.append("_No diagnostic steps recorded yet._")
    lines.append("")

    lines.append("## 4. Collected Evidence")
    if session and session.get("evidence"):
        for ev in session["evidence"]:
            lines.append(
                f"- **[{ev['step_id']} | {ev['evidence_type']} | source: {ev['source']}]** "
                f"{ev['description']}"
            )
    else:
        lines.append("_No diagnostic evidence collected yet._")
    lines.append("")

    lines.append("## 5. Ruled-Out Causes")
    if session and session.get("ruled_out_causes"):
        for item in session["ruled_out_causes"]:
            lines.append(f"- {item}")
    else:
        lines.append("_None explicitly ruled out._")
    lines.append("")

    lines.extend(
        [
            "## 6. Findings & Root Cause Status",
            f"- **Root Cause Status:** {report_data['root_cause_status']}",
        ]
    )
    if findings:
        for finding in findings:
            lines.append(
                f"- **[{finding['status'].upper()}]** ({finding['step_id']}): {finding['description']}"
            )
    else:
        lines.append("- _No diagnostic findings recorded._")
    lines.append("")

    lines.append("## 7. Resolution & Recommendations")
    if inc.get("resolution_notes"):
        lines.append(f"- **Resolution Recorded:** {inc['resolution_notes']}")
    for rec in report_data.get("recommendations", []):
        lines.append(f"- **Recommendation:** {rec}")

    return "\n".join(lines).strip() + "\n"


def render_printable_html_report(report_data: dict[str, Any]) -> str:
    """Render a clean, self-contained printable HTML incident handoff report."""
    inc = report_data["incident"]
    session = report_data.get("session")
    findings = report_data.get("findings", [])

    def esc(value: Any) -> str:
        return html.escape(str(value if value is not None else ""))

    safety_html = ""
    if session and session.get("safety_alert"):
        alert = session["safety_alert"]
        safety_html = (
            "<section class='safety-box'>"
            f"<h2>SAFETY STOP ALERT ({esc(alert['flag_id'])})</h2>"
            f"<p><strong>Trigger:</strong> {esc(alert['label'])}</p>"
            f"<p><strong>Warning:</strong> {esc(alert['warning_message'])}</p>"
            f"<p><strong>Required Action:</strong> {esc(alert['escalation_instruction'])}</p>"
            "</section>"
        )

    steps_items = "".join(
        f"<li><strong>{esc(s['step_id'])} — {esc(s['step_title'])}</strong> "
        f"[<code>{esc(s['result_code'])}</code> &rarr; <code>{esc(s['action_taken'])}</code>]: "
        f"{esc(s['summary'])}</li>"
        for s in (session.get("history", []) if session else [])
    ) or "<li><em>No diagnostic steps recorded yet.</em></li>"

    evidence_items = "".join(
        f"<li><strong>[{esc(e['step_id'])} | {esc(e['evidence_type'])}]</strong> "
        f"{esc(e['description'])} <em>(source: {esc(e['source'])})</em></li>"
        for e in (session.get("evidence", []) if session else [])
    ) or "<li><em>No evidence recorded yet.</em></li>"

    ruled_out_items = "".join(
        f"<li>{esc(item)}</li>"
        for item in (session.get("ruled_out_causes", []) if session else [])
    ) or "<li><em>None explicitly ruled out.</em></li>"

    finding_items = "".join(
        f"<li><strong>[{esc(f['status'].upper())}]</strong> ({esc(f['step_id'])}): "
        f"{esc(f['description'])}</li>"
        for f in findings
    ) or "<li><em>No diagnostic findings recorded.</em></li>"

    rec_items = "".join(
        f"<li>{esc(rec)}</li>" for rec in report_data.get("recommendations", [])
    )

    resolution_html = (
        f"<p><strong>Resolution Recorded:</strong> {esc(inc['resolution_notes'])}</p>"
        if inc.get("resolution_notes")
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Incident Report {esc(inc['incident_id'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1e293b; max-width: 860px; margin: 24px auto; padding: 0 16px; line-height: 1.5; }}
    h1 {{ border-bottom: 2px solid #0f172a; padding-bottom: 8px; font-size: 1.5rem; }}
    h2 {{ color: #0f172a; margin-top: 20px; font-size: 1.15rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
    .meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 16px; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; }}
    .safety-box {{ background: #fef2f2; border: 2px solid #dc2626; padding: 12px 16px; border-radius: 6px; margin: 16px 0; }}
    .safety-box h2 {{ color: #b91c1c; border-bottom: none; margin-top: 0; }}
    code {{ background: #f1f5f9; padding: 1px 5px; border-radius: 4px; font-size: 0.9em; }}
    @media print {{ body {{ margin: 0; max-width: none; }} }}
  </style>
</head>
<body>
  <h1>IT Incident &amp; Escalation Handoff Report ({esc(inc['incident_id'])})</h1>
  <div class="meta">
    <div><strong>Status:</strong> <code>{esc(inc['status'])}</code></div>
    <div><strong>Target OS:</strong> <code>{esc(inc['target_os'])}</code></div>
    <div><strong>Device Type:</strong> <code>{esc(inc.get('device_type') or 'unknown')}</code></div>
    <div><strong>Category:</strong> <code>{esc(inc.get('category') or 'unclassified')}</code></div>
    <div><strong>Workflow:</strong> <code>{esc(inc.get('workflow_id') or 'N/A')}</code> ({esc(report_data.get('workflow_name') or 'Not started')})</div>
    <div><strong>Created (UTC):</strong> {esc(inc['created_at'])}</div>
  </div>
  {safety_html}
  <h2>Reported Symptoms</h2>
  <p>{esc(inc['description'])}</p>
  <h2>Diagnostic Steps Performed</h2>
  <ol>{steps_items}</ol>
  <h2>Collected Evidence</h2>
  <ul>{evidence_items}</ul>
  <h2>Ruled-Out Causes</h2>
  <ul>{ruled_out_items}</ul>
  <h2>Findings &amp; Root Cause Status</h2>
  <p><strong>Root Cause Status:</strong> {esc(report_data['root_cause_status'])}</p>
  <ul>{finding_items}</ul>
  <h2>Resolution &amp; Recommendations</h2>
  {resolution_html}
  <ul>{rec_items}</ul>
</body>
</html>
"""
