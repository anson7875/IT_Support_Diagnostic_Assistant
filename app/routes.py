"""Flask routes for the IT Support Diagnostic & Case Management web interface."""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)

from app.diagnostic.diagnostic_engine import DiagnosticEngineError
from app.diagnostic.output_parser import parse_command_output
from app.i18n import get_translations
from app.services.incident_service import IncidentService
from app.services.report_service import (
    build_report_data,
    render_markdown_report,
    render_printable_html_report,
)

bp = Blueprint("main", __name__)


def _service() -> IncidentService:
    return current_app.config["INCIDENT_SERVICE"]


def _lang() -> str:
    return flask_session.get("lang", "zh")


@bp.app_context_processor
def inject_i18n() -> dict[str, object]:
    lang = _lang()
    return {"lang": lang, "t": get_translations(lang)}


@bp.route("/set-lang/<lang_code>")
def set_language(lang_code: str):
    if lang_code in ("zh", "en"):
        flask_session["lang"] = lang_code
    next_url = request.referrer or url_for("main.index")
    return redirect(next_url)


@bp.route("/")
def index():
    service = _service()
    incidents = service.list_incidents(limit=25)
    workflows = service.kb.list_workflows()
    return render_template("index.html", incidents=incidents, workflows=workflows)


@bp.route("/incidents/create", methods=["POST"])
def create_incident():
    service = _service()
    description = (request.form.get("description") or "").strip()
    target_os = (request.form.get("target_os") or "").strip() or None
    workflow_id = (request.form.get("workflow_id") or "").strip() or None

    if not description:
        return redirect(url_for("main.index"))

    result = service.create_incident(
        description=description,
        target_os=target_os,
        workflow_id=workflow_id,
    )
    incident = result["incident"]
    diag_session = result["session"]

    if diag_session:
        return redirect(
            url_for("main.view_session", session_id=diag_session["session_id"])
        )

    return render_template(
        "select_workflow.html",
        incident=incident,
        classification=result["classification"],
        workflows=service.kb.list_workflows(),
    )


@bp.route("/incidents/<incident_id>/start", methods=["POST"])
def start_workflow_for_incident(incident_id: str):
    service = _service()
    workflow_id = (request.form.get("workflow_id") or "").strip()
    target_os = (request.form.get("target_os") or "windows").strip()
    if not workflow_id:
        abort(400, "workflow_id is required")

    try:
        diag_session = service.start_session_for_incident(
            incident_id=incident_id,
            workflow_id=workflow_id,
            target_os=target_os,
        )
    except (KeyError, DiagnosticEngineError) as exc:
        abort(400, str(exc))

    return redirect(url_for("main.view_session", session_id=diag_session.session_id))


@bp.route("/session/<session_id>")
def view_session(session_id: str):
    service = _service()
    try:
        diag_session = service.load_session(session_id)
    except KeyError:
        abort(404)

    incident = service.get_incident(diag_session.incident_id)
    if diag_session.status != "active" or diag_session.current_step_id is None:
        return redirect(
            url_for("main.view_report", incident_id=diag_session.incident_id)
        )

    step = service.get_current_step(session_id)
    workflow = service.kb.get_workflow(diag_session.workflow_id)
    return render_template(
        "session.html",
        incident=incident,
        session=diag_session,
        workflow=workflow,
        step=step,
    )


@bp.route("/session/<session_id>/submit", methods=["POST"])
def submit_step(session_id: str):
    service = _service()
    safety_flag_id = (request.form.get("safety_flag_id") or "").strip() or None
    selection = (request.form.get("selection") or "").strip()
    raw_command_output = (request.form.get("raw_command_output") or "").strip() or None
    user_notes = (request.form.get("user_notes") or "").strip()

    outcome_id: str | None = None
    result_code: str | None = None
    if selection.startswith("outcome:"):
        outcome_id = selection.split(":", 1)[1]
    elif selection.startswith("fallback:"):
        result_code = selection.split(":", 1)[1]

    try:
        diag_session = service.load_session(session_id)
        res = service.submit_step(
            session_id=session_id,
            outcome_id=outcome_id,
            result_code=result_code,
            raw_command_output=raw_command_output,
            user_notes=user_notes,
            safety_flag_id=safety_flag_id,
        )
    except (KeyError, DiagnosticEngineError, ValueError) as exc:
        abort(400, str(exc))

    if res["status"] == "active":
        return redirect(url_for("main.view_session", session_id=session_id))
    return redirect(url_for("main.view_report", incident_id=diag_session.incident_id))


@bp.route("/api/parse-output", methods=["POST"])
def api_parse_output():
    payload = request.get_json(silent=True) or {}
    parser_key = payload.get("parser_key")
    raw_output = payload.get("raw_output", "")
    target_os = payload.get("target_os", "windows")

    if not parser_key:
        return jsonify({"error": "parser_key is required"}), 400

    try:
        parsed = parse_command_output(parser_key, raw_output, target_os=target_os)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(parsed.to_dict())


@bp.route("/incidents/<incident_id>/report")
def view_report(incident_id: str):
    service = _service()
    try:
        report_data = build_report_data(service, incident_id)
    except KeyError:
        abort(404)

    markdown_text = render_markdown_report(report_data)
    return render_template(
        "report.html",
        report=report_data,
        markdown_text=markdown_text,
    )


@bp.route("/incidents/<incident_id>/report/print")
def view_printable_report(incident_id: str):
    service = _service()
    try:
        report_data = build_report_data(service, incident_id)
    except KeyError:
        abort(404)

    html_doc = render_printable_html_report(report_data)
    return Response(html_doc, mimetype="text/html; charset=utf-8")


@bp.route("/incidents/<incident_id>/report/markdown")
def download_markdown_report(incident_id: str):
    service = _service()
    try:
        report_data = build_report_data(service, incident_id)
    except KeyError:
        abort(404)

    markdown_text = render_markdown_report(report_data)
    return Response(
        markdown_text,
        mimetype="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{incident_id}_report.md"'
        },
    )


@bp.route("/incidents/<incident_id>/resolution", methods=["POST"])
def record_resolution(incident_id: str):
    service = _service()
    resolution_notes = (request.form.get("resolution_notes") or "").strip()
    confirm_id_raw = (request.form.get("confirm_finding_id") or "").strip()
    confirm_finding_id = int(confirm_id_raw) if confirm_id_raw.isdigit() else None

    try:
        service.record_resolution(
            incident_id=incident_id,
            resolution_notes=resolution_notes,
            confirm_finding_id=confirm_finding_id,
        )
    except KeyError:
        abort(404)

    return redirect(url_for("main.view_report", incident_id=incident_id))
