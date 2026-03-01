import json
import sqlite3
from datetime import datetime
from pathlib import Path
import csv
from typing import List

from scout_assistant.models import RecruiterLead

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "leads.db"
JSON_PATH = DATA_DIR / "leads.json"
CSV_PATH = DATA_DIR / "leads.csv"


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recruiter_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                source_url TEXT NOT NULL,
                linkedin_url TEXT,
                public_email TEXT,
                confidence TEXT NOT NULL,
                confidence_reason TEXT NOT NULL,
                match_reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_leads(leads: List[RecruiterLead]) -> None:
    """Persist leads into local SQLite and JSON."""
    _ensure_storage()
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executemany(
            """
            INSERT INTO recruiter_leads (
                name, title, company, source_url, linkedin_url, public_email,
                confidence, confidence_reason, match_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    lead.name,
                    lead.title,
                    lead.company,
                    lead.source_url,
                    lead.linkedin_url,
                    lead.public_email,
                    lead.confidence,
                    lead.confidence_reason,
                    lead.match_reason,
                    now,
                )
                for lead in leads
            ],
        )
        conn.commit()
    finally:
        conn.close()

    payload = []
    if JSON_PATH.exists():
        try:
            payload = json.loads(JSON_PATH.read_text())
        except Exception:
            payload = []

    for lead in leads:
        row = lead.to_dict()
        row["created_at"] = now
        payload.append(row)
    JSON_PATH.write_text(json.dumps(payload, indent=2))

    with CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "title",
                "company",
                "source_url",
                "linkedin_url",
                "public_email",
                "confidence",
                "confidence_reason",
                "match_reason",
                "created_at",
            ],
        )
        writer.writeheader()
        for row in payload:
            writer.writerow(row)
