from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(os.getenv("RESCAM_DATA_DIR", Path.home() / ".rescam"))
DB_PATH = DATA_DIR / "rescam.sqlite3"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                visited_at TEXT NOT NULL,
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
            )
        """)
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_campaign(campaign: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO campaigns (id, created_at, details) VALUES (?, ?, ?)",
            (campaign["id"], campaign["created_at"], json.dumps(campaign)),
        )


def get_campaign(campaign_id: str) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute(
            "SELECT details FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
    return json.loads(row["details"]) if row else None


def record_visit(campaign_id: str, visited_at: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO visits (campaign_id, visited_at) VALUES (?, ?)",
            (campaign_id, visited_at),
        )


def list_campaigns() -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT c.details, COUNT(v.id) AS visits "
            "FROM campaigns c LEFT JOIN visits v ON v.campaign_id = c.id "
            "GROUP BY c.id ORDER BY c.created_at DESC"
        ).fetchall()
    result = []
    for row in rows:
        item = json.loads(row["details"])
        item["visit_count"] = row["visits"]
        result.append(item)
    return result
