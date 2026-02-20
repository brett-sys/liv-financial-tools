"""Web Push notification helpers.

Uses pywebpush to send push notifications via VAPID.
Subscriptions are stored in a simple SQLite table.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import config

DB_PATH = config.BASE_DIR / "push_subscriptions.db"

try:
    from pywebpush import webpush, WebPushException
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False


@contextmanager
def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL DEFAULT '',
            endpoint TEXT NOT NULL UNIQUE,
            subscription_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


def save_subscription(agent_name, subscription_info):
    """Store or update a push subscription."""
    sub_json = json.dumps(subscription_info)
    endpoint = subscription_info.get("endpoint", "")
    with _get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO subscriptions (agent_name, endpoint, subscription_json) VALUES (?, ?, ?)",
            (agent_name, endpoint, sub_json),
        )
        conn.commit()


def get_all_subscriptions():
    with _get_db() as conn:
        rows = conn.execute("SELECT * FROM subscriptions").fetchall()
    return [dict(r) for r in rows]


def remove_subscription(endpoint):
    with _get_db() as conn:
        conn.execute("DELETE FROM subscriptions WHERE endpoint = ?", (endpoint,))
        conn.commit()


def send_push(subscription_info, title, body, url="/dashboard", tag="follow-up"):
    """Send a push notification to a single subscription."""
    if not PUSH_AVAILABLE:
        return False
    if not config.VAPID_PRIVATE_KEY:
        return False

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "tag": tag,
    })

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=config.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{config.VAPID_CLAIMS_EMAIL}"},
        )
        return True
    except WebPushException as e:
        if e.response and e.response.status_code in (404, 410):
            endpoint = subscription_info.get("endpoint", "")
            remove_subscription(endpoint)
        return False
    except Exception:
        return False


def send_follow_up_reminders():
    """Send push notifications for follow-ups due today. Called by scheduler."""
    from models.calls import get_stats
    stats = get_stats()
    due_today = stats.get("due_today", [])

    if not due_today:
        return

    subs = get_all_subscriptions()
    if not subs:
        return

    count = len(due_today)
    names = ", ".join(d["contact_name"] for d in due_today[:3])
    if count > 3:
        names += f" +{count - 3} more"

    for sub in subs:
        try:
            sub_info = json.loads(sub["subscription_json"])
            send_push(
                sub_info,
                title=f"{count} Follow-up{'s' if count > 1 else ''} Due Today",
                body=names,
                url="/dashboard",
            )
        except Exception:
            pass
