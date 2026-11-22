"""IT Support Diagnostic & Case Management System application factory."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from app.database.db import Database
from app.knowledge.knowledge_base import KnowledgeBase
from app.routes import bp
from app.services.incident_service import IncidentService


def create_app(
    db_path: str | Path | None = None,
    data_dir: str | Path | None = None,
    testing: bool = False,
) -> Flask:
    """Create and configure the Flask web application."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-it-support-diagnostic-key")
    app.config["TESTING"] = testing

    db = Database(db_path=db_path)
    db.init_db()

    kb = KnowledgeBase(data_dir=data_dir)
    kb.load_all()

    app.config["DATABASE"] = db
    app.config["KNOWLEDGE_BASE"] = kb
    app.config["INCIDENT_SERVICE"] = IncidentService(db, kb)

    app.register_blueprint(bp)
    return app
