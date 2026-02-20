"""SQLite-backed referral management."""

import sqlite3
from datetime import date, datetime

from config import REFERRALS_DB_PATH

STATUSES = ["New", "Contacted", "Quoted", "Applied", "Sold", "Lost"]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(REFERRALS_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_name TEXT NOT NULL,
            referred_name TEXT NOT NULL,
            referred_phone TEXT DEFAULT '',
            referred_email TEXT DEFAULT '',
            date_added TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            notes TEXT DEFAULT '',
            premium_sold TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def add_referral(referrer_name, referred_name, phone="", email="", notes=""):
    conn = _get_conn()
    now = datetime.now().isoformat()
    today = date.today().isoformat()
    cur = conn.execute(
        "INSERT INTO referrals (referrer_name, referred_name, referred_phone, "
        "referred_email, date_added, status, notes, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'New', ?, ?)",
        (referrer_name, referred_name, phone, email, today, notes, now),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_all_referrals():
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM referrals ORDER BY date_added DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_referral(row_id):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM referrals WHERE id = ?", (row_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_status(row_id, new_status, premium=""):
    conn = _get_conn()
    now = datetime.now().isoformat()
    if premium:
        conn.execute(
            "UPDATE referrals SET status=?, premium_sold=?, updated_at=? WHERE id=?",
            (new_status, premium, now, row_id),
        )
    else:
        conn.execute(
            "UPDATE referrals SET status=?, updated_at=? WHERE id=?",
            (new_status, now, row_id),
        )
    conn.commit()
    conn.close()


def delete_referral(row_id):
    conn = _get_conn()
    conn.execute("DELETE FROM referrals WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM referrals").fetchone()[0]
    sold = conn.execute("SELECT COUNT(*) FROM referrals WHERE status='Sold'").fetchone()[0]
    lost = conn.execute("SELECT COUNT(*) FROM referrals WHERE status='Lost'").fetchone()[0]

    top = conn.execute(
        "SELECT referrer_name, COUNT(*) as cnt FROM referrals "
        "GROUP BY referrer_name ORDER BY cnt DESC LIMIT 5"
    ).fetchall()

    thankyou = conn.execute(
        "SELECT referrer_name, referred_name FROM referrals WHERE status='Sold' "
        "ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()

    conn.close()

    conversion = (sold / total * 100) if total > 0 else 0
    closed_total = sold + lost
    close_rate = (sold / closed_total * 100) if closed_total > 0 else 0

    return {
        "total": total,
        "sold": sold,
        "lost": lost,
        "conversion_pct": conversion,
        "close_rate_pct": close_rate,
        "top_referrers": [(r["referrer_name"], r["cnt"]) for r in top],
        "thankyou_list": [(r["referrer_name"], r["referred_name"]) for r in thankyou],
    }
