"""SQLite database persistence package."""

from app.database.db import Database, DatabaseError

__all__ = ["Database", "DatabaseError"]
