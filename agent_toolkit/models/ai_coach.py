"""SQLite storage for the AI coaching suite (Illuminate).

Holds the editable Operating Principles config and saved Presentation Review
results so agents can track their score over time. We intentionally do NOT
store full call transcripts here (they contain PII / health info) — only the
structured evaluation and an optional agent-supplied label.
"""

import json
import sqlite3
from contextlib import contextmanager

from config import AI_COACH_DB_PATH
from ai.prompts import DEFAULT_OPERATING_PRINCIPLES

OPERATING_PRINCIPLES_KEY = "operating_principles"


@contextmanager
def get_db():
    conn = sqlite3.connect(str(AI_COACH_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL DEFAULT '',
                label TEXT NOT NULL DEFAULT '',
                score INTEGER NOT NULL DEFAULT 0,
                verdict TEXT NOT NULL DEFAULT '',
                categories_json TEXT NOT NULL DEFAULT '[]',
                fixes_json TEXT NOT NULL DEFAULT '[]',
                model TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_debriefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL DEFAULT '',
                personality TEXT NOT NULL DEFAULT '',
                difficulty TEXT NOT NULL DEFAULT '',
                product TEXT NOT NULL DEFAULT '',
                outcome TEXT NOT NULL DEFAULT '',
                score INTEGER NOT NULL DEFAULT 0,
                headline TEXT NOT NULL DEFAULT '',
                did_well_json TEXT NOT NULL DEFAULT '[]',
                missed_json TEXT NOT NULL DEFAULT '[]',
                one_thing TEXT NOT NULL DEFAULT '',
                best_line TEXT NOT NULL DEFAULT '',
                turns INTEGER NOT NULL DEFAULT 0,
                model TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# Operating Principles (the shared config)
# ---------------------------------------------------------------------------

def get_operating_principles() -> str:
    """Return the saved Operating Principles, or the baked-in default."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM ai_settings WHERE key = ?", (OPERATING_PRINCIPLES_KEY,)
        ).fetchone()
    if row and row["value"].strip():
        return row["value"]
    return DEFAULT_OPERATING_PRINCIPLES


def save_operating_principles(text: str):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO ai_settings (key, value, updated_at)
               VALUES (?, ?, datetime('now', 'localtime'))
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   updated_at = excluded.updated_at""",
            (OPERATING_PRINCIPLES_KEY, text),
        )
        conn.commit()


def is_using_default_principles() -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM ai_settings WHERE key = ?", (OPERATING_PRINCIPLES_KEY,)
        ).fetchone()
    return not (row and row["value"].strip())


# ---------------------------------------------------------------------------
# Presentation Reviews
# ---------------------------------------------------------------------------

def save_review(agent_name: str, label: str, result: dict, model: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO ai_reviews
               (agent_name, label, score, verdict, categories_json, fixes_json, model)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_name,
                label,
                int(result.get("score", 0)),
                result.get("verdict", ""),
                json.dumps(result.get("categories", [])),
                json.dumps(result.get("fixes", [])),
                model,
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_reviews(agent_name: str | None = None, limit: int = 100) -> list:
    clauses, params = [], []
    if agent_name:
        clauses.append("agent_name = ?")
        params.append(agent_name)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT id, agent_name, label, score, verdict, model, created_at "
            f"FROM ai_reviews {where} ORDER BY id DESC LIMIT ?",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def get_review(review_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM ai_reviews WHERE id = ?", (review_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["categories"] = json.loads(data.pop("categories_json") or "[]")
    data["fixes"] = json.loads(data.pop("fixes_json") or "[]")
    return data


# ---------------------------------------------------------------------------
# Roleplay Debriefs (Tool 2)
# ---------------------------------------------------------------------------

def save_debrief(agent_name: str, personality: str, difficulty: str, product: str,
                 result: dict, turns: int, model: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO ai_debriefs
               (agent_name, personality, difficulty, product, outcome, score,
                headline, did_well_json, missed_json, one_thing, best_line, turns, model)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_name, personality, difficulty, product,
                result.get("outcome", ""),
                int(result.get("score", 0)),
                result.get("headline", ""),
                json.dumps(result.get("did_well", [])),
                json.dumps(result.get("missed", [])),
                result.get("one_thing", ""),
                result.get("best_line", ""),
                int(turns),
                model,
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_debriefs(agent_name: str | None = None, limit: int = 100) -> list:
    clauses, params = [], []
    if agent_name:
        clauses.append("agent_name = ?")
        params.append(agent_name)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT id, agent_name, personality, difficulty, product, outcome, "
            f"score, headline, turns, model, created_at "
            f"FROM ai_debriefs {where} ORDER BY id DESC LIMIT ?",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def get_debrief(debrief_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM ai_debriefs WHERE id = ?", (debrief_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["did_well"] = json.loads(data.pop("did_well_json") or "[]")
    data["missed"] = json.loads(data.pop("missed_json") or "[]")
    return data
