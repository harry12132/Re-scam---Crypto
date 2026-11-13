from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("RESCAM_DATA_DIR", Path.home() / ".rescam"))
DB_PATH = DATA_DIR / "rescam.sqlite3"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
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
    db.commit()
    return db


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
