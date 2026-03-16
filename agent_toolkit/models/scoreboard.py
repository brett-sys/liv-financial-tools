"""Scoreboard database model — tracks agent activity across key metrics."""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

import config

DB_PATH = config.BASE_DIR / "scoreboard.db"

ACTIVITY_TYPES = ["policy", "application", "call", "appointment", "presentation"]

ACTIVITY_LABELS = {
    "policy": "Policy",
    "application": "Application",
    "call": "Call",
    "appointment": "Appointment",
    "presentation": "Presentation",
}

ACTIVITY_EMOJIS = {
    "policy": "💰",
    "application": "📋",
    "call": "📞",
    "appointment": "📅",
    "presentation": "🎯",
}

MILESTONES = {
    "policy": [1, 5, 10, 20, 30, 50],
    "call": [25, 50, 100, 250, 500],
    "appointment": [5, 10, 25, 50],
    "presentation": [5, 10, 25, 50],
    "application": [5, 10, 25, 50],
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                ap_amount REAL NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def log_activity(agent_name: str, activity_type: str, count: int = 1,
                 ap_amount: float = 0.0, notes: str = "") -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO activities (agent_name, activity_type, count, ap_amount, notes, logged_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (agent_name, activity_type, count, ap_amount, notes,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return cur.lastrowid


def _date_filter(period: str):
    today = date.today()
    if period == "today":
        return today.isoformat(), today.isoformat()
    if period == "week":
        monday = today - timedelta(days=today.weekday())
        return monday.isoformat(), today.isoformat()
    if period == "month":
        return today.replace(day=1).isoformat(), today.isoformat()
    return "2000-01-01", today.isoformat()


def get_leaderboard(period: str = "week") -> dict:
    """Return leaderboard data for all agents across all metrics."""
    start, end = _date_filter(period)
    agents = config.AGENT_CHOICES

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """SELECT agent_name, activity_type,
                      SUM(count) as total_count,
                      SUM(ap_amount) as total_ap
               FROM activities
               WHERE date(logged_at) BETWEEN ? AND ?
               GROUP BY agent_name, activity_type""",
            (start, end),
        ).fetchall()

    data: dict[str, dict] = {
        a: {"policies": 0, "ap": 0.0, "calls": 0,
            "appointments": 0, "presentations": 0, "applications": 0}
        for a in agents
    }
    for row in rows:
        agent = row["agent_name"]
        if agent not in data:
            data[agent] = {"policies": 0, "ap": 0.0, "calls": 0,
                           "appointments": 0, "presentations": 0, "applications": 0}
        atype = row["activity_type"]
        if atype == "policy":
            data[agent]["policies"] += row["total_count"]
            data[agent]["ap"] += row["total_ap"] or 0
        elif atype == "call":
            data[agent]["calls"] += row["total_count"]
        elif atype == "appointment":
            data[agent]["appointments"] += row["total_count"]
        elif atype == "presentation":
            data[agent]["presentations"] += row["total_count"]
        elif atype == "application":
            data[agent]["applications"] += row["total_count"]

    return data


def get_agent_totals(agent_name: str, period: str = "week") -> dict:
    """Get totals for a single agent."""
    lb = get_leaderboard(period)
    return lb.get(agent_name, {})


def get_ranked(metric: str, period: str = "week") -> list[dict]:
    """Return agents ranked by a given metric."""
    data = get_leaderboard(period)
    key_map = {
        "policies": "policies", "ap": "ap", "calls": "calls",
        "appointments": "appointments", "presentations": "presentations",
        "applications": "applications",
    }
    key = key_map.get(metric, "policies")
    ranked = sorted(
        [{"agent": a, **stats} for a, stats in data.items()],
        key=lambda x: x[key],
        reverse=True,
    )
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return ranked


def get_all_time_totals(agent_name: str, activity_type: str) -> int:
    """Get all-time count for milestone checking."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT SUM(count) FROM activities WHERE agent_name=? AND activity_type=?",
            (agent_name, activity_type),
        ).fetchone()
    return int(row[0] or 0)


def check_milestone(agent_name: str, activity_type: str) -> int | None:
    """Return milestone value if agent just hit one, else None."""
    total = get_all_time_totals(agent_name, activity_type)
    for m in MILESTONES.get(activity_type, []):
        if total == m:
            return m
    return None


def get_recent_activity(limit: int = 20) -> list[dict]:
    """Recent activity feed across all agents."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM activities ORDER BY logged_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
