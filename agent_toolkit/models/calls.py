"""SQLite database models and query helpers for call logging."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from config import CALLS_DB_PATH


@contextmanager
def get_db():
    conn = sqlite3.connect(str(CALLS_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                phone_number TEXT NOT NULL DEFAULT '',
                call_datetime TEXT NOT NULL,
                direction TEXT NOT NULL,
                outcome TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                follow_up_date TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        try:
            conn.execute("ALTER TABLE calls ADD COLUMN agent_name TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        conn.commit()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def log_call(agent_name, contact_name, phone_number, call_datetime, direction,
             outcome, notes="", follow_up_date=None):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO calls
               (agent_name, contact_name, phone_number, call_datetime,
                direction, outcome, notes, follow_up_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (agent_name, contact_name, phone_number, call_datetime,
             direction, outcome, notes, follow_up_date or None),
        )
        conn.commit()
        return cur.lastrowid


def update_call(call_id, **fields):
    allowed = {
        "agent_name", "contact_name", "phone_number", "call_datetime",
        "direction", "outcome", "notes", "follow_up_date",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [call_id]
    with get_db() as conn:
        conn.execute(f"UPDATE calls SET {set_clause} WHERE id = ?", values)
        conn.commit()


def delete_call(call_id):
    with get_db() as conn:
        conn.execute("DELETE FROM calls WHERE id = ?", (call_id,))
        conn.commit()


def get_call(call_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()


def get_calls(limit=200, offset=0, direction=None, outcome=None,
              search=None, date_from=None, date_to=None, agent_name=None):
    clauses = []
    params = []

    if agent_name:
        clauses.append("agent_name = ?")
        params.append(agent_name)
    if direction:
        clauses.append("direction = ?")
        params.append(direction)
    if outcome:
        clauses.append("outcome = ?")
        params.append(outcome)
    if search:
        clauses.append("(contact_name LIKE ? OR phone_number LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if date_from:
        clauses.append("call_datetime >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("call_datetime <= ?")
        params.append(date_to + " 23:59:59")

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM calls {where} ORDER BY call_datetime DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        return conn.execute(query, params).fetchall()


# ---------------------------------------------------------------------------
# Stats & reporting
# ---------------------------------------------------------------------------

def _week_bounds():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday.strftime("%Y-%m-%d"), friday.strftime("%Y-%m-%d")


def get_week_calls():
    mon, fri = _week_bounds()
    return get_calls(limit=9999, date_from=mon, date_to=fri)


def get_today_calls():
    today = datetime.now().strftime("%Y-%m-%d")
    return get_calls(limit=9999, date_from=today, date_to=today)


def get_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    mon, fri = _week_bounds()

    with get_db() as conn:
        today_count = conn.execute(
            "SELECT COUNT(*) FROM calls WHERE call_datetime >= ? AND call_datetime <= ?",
            (today, today + " 23:59:59"),
        ).fetchone()[0]

        week_count = conn.execute(
            "SELECT COUNT(*) FROM calls WHERE call_datetime >= ? AND call_datetime <= ?",
            (mon, fri + " 23:59:59"),
        ).fetchone()[0]

        outcomes = conn.execute(
            """SELECT outcome, COUNT(*) as cnt FROM calls
               WHERE call_datetime >= ? AND call_datetime <= ?
               GROUP BY outcome ORDER BY cnt DESC""",
            (mon, fri + " 23:59:59"),
        ).fetchall()

        follow_ups = conn.execute(
            """SELECT * FROM calls
               WHERE follow_up_date IS NOT NULL AND follow_up_date >= ?
               ORDER BY follow_up_date ASC LIMIT 10""",
            (today,),
        ).fetchall()

        # Per-agent stats for leaderboard
        agent_stats = conn.execute(
            """SELECT agent_name, COUNT(*) as cnt FROM calls
               WHERE call_datetime >= ? AND call_datetime <= ?
               AND agent_name != ''
               GROUP BY agent_name ORDER BY cnt DESC""",
            (mon, fri + " 23:59:59"),
        ).fetchall()

        # Due today follow-ups
        due_today = conn.execute(
            """SELECT * FROM calls
               WHERE follow_up_date = ?
               ORDER BY contact_name ASC""",
            (today,),
        ).fetchall()

    return {
        "today_count": today_count,
        "week_count": week_count,
        "outcomes": [{"outcome": r["outcome"], "count": r["cnt"]} for r in outcomes],
        "follow_ups": [dict(r) for r in follow_ups],
        "agent_stats": [{"agent": r["agent_name"], "count": r["cnt"]} for r in agent_stats],
        "due_today": [dict(r) for r in due_today],
    }


def get_contact_suggestions(query, limit=8):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT contact_name, phone_number, MAX(call_datetime) AS last_call
               FROM calls
               WHERE contact_name LIKE ? OR phone_number LIKE ?
               GROUP BY contact_name, phone_number
               ORDER BY last_call DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [{"name": r["contact_name"], "phone": r["phone_number"]} for r in rows]
