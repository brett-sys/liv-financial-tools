"""Scoreboard blueprint — leaderboard, activity logging, recognition."""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify,
)
from datetime import datetime

import config
from models.scoreboard import (
    log_activity, get_ranked, get_leaderboard, get_recent_activity,
    check_milestone, ACTIVITY_TYPES, ACTIVITY_LABELS, ACTIVITY_EMOJIS,
    init_db,
)
from slack_notify import notify_activity, notify_milestone, notify_daily_summary

scoreboard_bp = Blueprint("scoreboard", __name__)

with scoreboard_bp.app_context if hasattr(scoreboard_bp, "app_context") else (lambda: __import__("contextlib").nullcontext())():
    pass

PERIODS = {
    "today": "Today",
    "week": "This Week",
    "month": "This Month",
    "alltime": "All Time",
}

METRICS = {
    "policies": ("Policies", "💰"),
    "ap": ("Annual Premium", "💵"),
    "calls": ("Calls", "📞"),
    "appointments": ("Appointments", "📅"),
    "presentations": ("Presentations", "🎯"),
    "applications": ("Applications", "📋"),
}


@scoreboard_bp.route("/scoreboard")
def scoreboard():
    period = request.args.get("period", "week")
    metric = request.args.get("metric", "policies")

    if period not in PERIODS:
        period = "week"
    if metric not in METRICS:
        metric = "policies"

    ranked = get_ranked(metric, period)
    leaderboard = get_leaderboard(period)
    recent = get_recent_activity(15)

    # Build recognition badges
    recognition = _build_recognition(leaderboard)

    # Format recent feed
    feed = []
    for r in recent:
        emoji = ACTIVITY_EMOJIS.get(r["activity_type"], "✅")
        label = ACTIVITY_LABELS.get(r["activity_type"], r["activity_type"])
        ap_str = f" · ${r['ap_amount']:,.0f} AP" if r.get("ap_amount") else ""
        feed.append({
            **r,
            "emoji": emoji,
            "label": label,
            "ap_str": ap_str,
            "time_str": _time_ago(r["logged_at"]),
        })

    return render_template(
        "scoreboard.html",
        ranked=ranked,
        leaderboard=leaderboard,
        recent_feed=feed,
        recognition=recognition,
        period=period,
        metric=metric,
        periods=PERIODS,
        metrics=METRICS,
        agents=config.AGENT_CHOICES,
    )


@scoreboard_bp.route("/scoreboard/log", methods=["GET", "POST"])
def log():
    agent_pref = request.cookies.get("agent_pref", config.AGENT_CHOICES[0])

    if request.method == "POST":
        agent = request.form.get("agent_name", "").strip()
        activity_type = request.form.get("activity_type", "").strip()
        count = max(1, int(request.form.get("count", 1) or 1))
        notes = request.form.get("notes", "").strip()

        ap_amount = 0.0
        if activity_type == "policy":
            try:
                ap_amount = float(
                    request.form.get("ap_amount", "0").replace(",", "").replace("$", "") or 0
                )
            except ValueError:
                ap_amount = 0.0

        if not agent or activity_type not in ACTIVITY_TYPES:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("scoreboard.log"))

        log_activity(agent, activity_type, count, ap_amount, notes)

        # Slack notification
        notify_activity(agent, activity_type, count, ap_amount, notes)

        # Check for milestone
        milestone = check_milestone(agent, activity_type)
        if milestone:
            notify_milestone(agent, activity_type, milestone)
            flash(f"🏆 MILESTONE! {agent} hit {milestone} {activity_type}s all-time!", "success")

        label = ACTIVITY_LABELS.get(activity_type, activity_type)
        ap_msg = f" (${ap_amount:,.0f} AP)" if ap_amount else ""
        flash(f"✅ Logged {count}x {label}{ap_msg} for {agent}!", "success")
        return redirect(url_for("scoreboard.scoreboard"))

    return render_template(
        "log_activity.html",
        agents=config.AGENT_CHOICES,
        activity_types=ACTIVITY_TYPES,
        activity_labels=ACTIVITY_LABELS,
        activity_emojis=ACTIVITY_EMOJIS,
        default_agent=agent_pref,
    )


@scoreboard_bp.route("/scoreboard/summary", methods=["POST"])
def post_summary():
    """Manually trigger a Slack summary post."""
    period = request.form.get("period", "today")
    ranked = get_ranked("policies", period)
    notify_daily_summary(ranked, period)
    flash("📊 Summary posted to Slack!", "success")
    return redirect(url_for("scoreboard.scoreboard"))


@scoreboard_bp.route("/scoreboard/api/leaderboard")
def api_leaderboard():
    period = request.args.get("period", "week")
    return jsonify(get_leaderboard(period))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_recognition(leaderboard: dict) -> list[dict]:
    """Build recognition badges from leaderboard data."""
    badges = []
    if not leaderboard:
        return badges

    # Top Closer (most policies)
    top_policy = max(leaderboard.items(), key=lambda x: x[1]["policies"], default=None)
    if top_policy and top_policy[1]["policies"] > 0:
        badges.append({
            "title": "Top Closer",
            "emoji": "🏆",
            "agent": top_policy[0],
            "stat": f"{top_policy[1]['policies']} {'policy' if top_policy[1]['policies'] == 1 else 'policies'}",
            "color": "#ffd700",
        })

    # Most AP
    top_ap = max(leaderboard.items(), key=lambda x: x[1]["ap"], default=None)
    if top_ap and top_ap[1]["ap"] > 0:
        badges.append({
            "title": "Premium Leader",
            "emoji": "💵",
            "agent": top_ap[0],
            "stat": f"${top_ap[1]['ap']:,.0f} AP",
            "color": "#34c759",
        })

    # Iron Man (most calls)
    top_calls = max(leaderboard.items(), key=lambda x: x[1]["calls"], default=None)
    if top_calls and top_calls[1]["calls"] > 0:
        badges.append({
            "title": "Iron Man",
            "emoji": "📞",
            "agent": top_calls[0],
            "stat": f"{top_calls[1]['calls']} calls",
            "color": "#4f8cff",
        })

    # Appointment King
    top_appt = max(leaderboard.items(), key=lambda x: x[1]["appointments"], default=None)
    if top_appt and top_appt[1]["appointments"] > 0:
        badges.append({
            "title": "Appointment King",
            "emoji": "📅",
            "agent": top_appt[0],
            "stat": f"{top_appt[1]['appointments']} appointments",
            "color": "#ff9f0a",
        })

    return badges


def _time_ago(logged_at: str) -> str:
    try:
        dt = datetime.strptime(logged_at, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - dt
        s = int(diff.total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            return f"{s // 60}m ago"
        if s < 86400:
            return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return logged_at
