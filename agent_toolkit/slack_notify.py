"""Slack webhook notifications for scoreboard events."""

import json
import os
import threading

try:
    import requests as _requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False


def _webhook_url() -> str:
    return os.getenv("SLACK_WEBHOOK_URL", "")


def _post(payload: dict):
    url = _webhook_url()
    if not url or not _REQUESTS_OK:
        return
    try:
        _requests.post(url, data=json.dumps(payload), timeout=5,
                       headers={"Content-Type": "application/json"})
    except Exception:
        pass


def _bg(payload: dict):
    threading.Thread(target=_post, args=(payload,), daemon=True).start()


# ---------------------------------------------------------------------------
# Public notification functions
# ---------------------------------------------------------------------------

def notify_activity(agent: str, activity_type: str, count: int,
                    ap_amount: float = 0, notes: str = ""):
    """Post activity log to Slack."""
    emojis = {
        "policy": "💰", "application": "📋", "call": "📞",
        "appointment": "📅", "presentation": "🎯",
    }
    emoji = emojis.get(activity_type, "✅")
    label = activity_type.capitalize()

    if activity_type == "policy" and ap_amount:
        text = (
            f"{emoji} *{agent}* just wrote a policy!\n"
            f">*Annual Premium:* ${ap_amount:,.0f}"
        )
        if notes:
            text += f"\n>_{notes}_"
    else:
        qty = f"{count}x " if count > 1 else ""
        text = f"{emoji} *{agent}* logged {qty}{label}"
        if notes:
            text += f"\n>_{notes}_"

    _bg({"text": text})


def notify_milestone(agent: str, activity_type: str, milestone: int):
    """Post a milestone achievement to Slack."""
    emojis = {
        "policy": "🏆", "call": "📞", "appointment": "🎯",
        "presentation": "🎤", "application": "📋",
    }
    label = activity_type.capitalize()
    emoji = emojis.get(activity_type, "🏆")

    text = (
        f"{emoji} *MILESTONE* {emoji}\n"
        f"*{agent}* just hit *{milestone} {label}s* all-time! "
        f"Let's go! 🔥🔥🔥"
    )
    _bg({"text": text})


def notify_daily_summary(summary: list[dict], period: str = "today"):
    """Post a daily/weekly leaderboard summary to Slack."""
    if not summary:
        return

    label = "Today" if period == "today" else "This Week"
    lines = [f"📊 *LIFI Scoreboard — {label}*\n"]

    medals = ["🥇", "🥈", "🥉"]
    for i, agent_data in enumerate(summary[:5]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        name = agent_data.get("agent", "")
        policies = agent_data.get("policies", 0)
        ap = agent_data.get("ap", 0)
        calls = agent_data.get("calls", 0)
        parts = []
        if policies:
            parts.append(f"{policies} {'policy' if policies == 1 else 'policies'}")
        if ap:
            parts.append(f"${ap:,.0f} AP")
        if calls:
            parts.append(f"{calls} calls")
        stat_str = " · ".join(parts) if parts else "No activity yet"
        lines.append(f"{medal} *{name}* — {stat_str}")

    _bg({"text": "\n".join(lines)})
