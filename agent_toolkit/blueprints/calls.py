"""Calls blueprint – leaderboard, call logging, history, GHL sync."""

from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    make_response,
)

import config
from models.calls import (
    log_call as db_log_call, update_call, delete_call, get_call,
    get_calls, get_stats, get_contact_suggestions,
)
from calendar_integration import get_calendar_urls, generate_ics
from ghl_integration import upsert_contact, GHLError
from push import save_subscription

calls_bp = Blueprint("calls", __name__)


# ---------------------------------------------------------------------------
# Leaderboard / Dashboard
# ---------------------------------------------------------------------------
@calls_bp.route("/dashboard")
def leaderboard():
    stats = get_stats()
    return render_template("leaderboard.html", stats=stats, now=datetime.now())


# ---------------------------------------------------------------------------
# Log a new call
# ---------------------------------------------------------------------------
@calls_bp.route("/log", methods=["GET", "POST"])
def log_call_route():
    if request.method == "POST":
        agent = request.form.get("agent_name", "").strip()
        contact = request.form.get("contact_name", "").strip()
        phone = request.form.get("phone_number", "").strip()

        db_log_call(
            agent_name=agent,
            contact_name=contact,
            phone_number=phone,
            call_datetime=request.form.get(
                "call_datetime", datetime.now().strftime("%Y-%m-%d %H:%M")
            ),
            direction=request.form.get("direction", "Outbound"),
            outcome=request.form.get("outcome", "Other"),
            notes=request.form.get("notes", "").strip(),
            follow_up_date=request.form.get("follow_up_date") or None,
        )

        follow_up = request.form.get("follow_up_date")
        if follow_up:
            cal = get_calendar_urls(
                agent_name=agent,
                contact_name=contact,
                phone_number=phone,
                follow_up_date=follow_up,
                notes=request.form.get("notes", "").strip(),
            )
            flash("Call logged!", "success")
            return render_template("cal_redirect.html", cal=cal)

        flash("Call logged!", "success")
        return redirect(url_for("calls.leaderboard"))

    return render_template(
        "log.html",
        directions=config.DIRECTION_CHOICES,
        outcomes=config.OUTCOME_CHOICES,
        now=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Edit call
# ---------------------------------------------------------------------------
@calls_bp.route("/edit/<int:call_id>", methods=["GET", "POST"])
def edit_call_route(call_id):
    call = get_call(call_id)
    if not call:
        flash("Call not found.", "error")
        return redirect(url_for("calls.history"))

    if request.method == "POST":
        update_call(
            call_id,
            agent_name=request.form.get("agent_name", "").strip(),
            contact_name=request.form.get("contact_name", "").strip(),
            phone_number=request.form.get("phone_number", "").strip(),
            call_datetime=request.form.get("call_datetime", ""),
            direction=request.form.get("direction", "Outbound"),
            outcome=request.form.get("outcome", "Other"),
            notes=request.form.get("notes", "").strip(),
            follow_up_date=request.form.get("follow_up_date") or None,
        )
        flash("Call updated.", "success")
        return redirect(url_for("calls.history"))

    return render_template(
        "edit.html",
        call=call,
        directions=config.DIRECTION_CHOICES,
        outcomes=config.OUTCOME_CHOICES,
    )


# ---------------------------------------------------------------------------
# Delete call
# ---------------------------------------------------------------------------
@calls_bp.route("/delete/<int:call_id>", methods=["POST"])
def delete_call_route(call_id):
    delete_call(call_id)
    flash("Call deleted.", "success")
    return redirect(url_for("calls.history"))


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
@calls_bp.route("/history")
def history():
    agent_name = request.args.get("agent_name", "")
    direction = request.args.get("direction", "")
    outcome = request.args.get("outcome", "")
    search = request.args.get("search", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    calls = get_calls(
        agent_name=agent_name or None,
        direction=direction or None,
        outcome=outcome or None,
        search=search or None,
        date_from=date_from or None,
        date_to=date_to or None,
    )
    return render_template(
        "history.html",
        calls=calls,
        directions=config.DIRECTION_CHOICES,
        outcomes=config.OUTCOME_CHOICES,
        filters={
            "agent_name": agent_name,
            "direction": direction,
            "outcome": outcome,
            "search": search,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


# ---------------------------------------------------------------------------
# Contact auto-suggest API
# ---------------------------------------------------------------------------
@calls_bp.route("/api/suggest")
def suggest():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    return jsonify(get_contact_suggestions(q))


# ---------------------------------------------------------------------------
# Manual export to Google Sheets
# ---------------------------------------------------------------------------
@calls_bp.route("/export", methods=["POST"])
def export_now():
    try:
        from sheets import export_week_to_sheets
        result = export_week_to_sheets()
        flash(f"Exported to Google Sheets: {result}", "success")
    except Exception as e:
        flash(f"Export failed: {e}", "error")
    return redirect(url_for("calls.leaderboard"))


# ---------------------------------------------------------------------------
# Calendar .ics download
# ---------------------------------------------------------------------------
@calls_bp.route("/calendar.ics")
def download_ics():
    contact = request.args.get("contact", "")
    phone = request.args.get("phone", "")
    date = request.args.get("date", "")
    notes = request.args.get("notes", "")
    if not date:
        flash("No follow-up date provided.", "error")
        return redirect(url_for("calls.leaderboard"))
    ics_content = generate_ics(contact, phone, date, notes)
    resp = make_response(ics_content)
    resp.headers["Content-Type"] = "text/calendar; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=follow_up.ics"
    return resp


# ---------------------------------------------------------------------------
# GHL manual sync
# ---------------------------------------------------------------------------
@calls_bp.route("/ghl-sync/<int:call_id>", methods=["POST"])
def ghl_sync(call_id):
    call = get_call(call_id)
    if not call:
        flash("Call not found.", "error")
        return redirect(url_for("calls.history"))

    try:
        contact_id = upsert_contact(
            name=call["contact_name"],
            phone=call["phone_number"],
        )
        flash(f"Synced {call['contact_name']} to Go High Level (ID: {contact_id})", "success")
    except GHLError as e:
        flash(f"GHL sync failed: {e}", "error")
    except Exception as e:
        flash(f"GHL sync error: {e}", "error")

    return redirect(request.referrer or url_for("calls.history"))


# ---------------------------------------------------------------------------
# Push subscription registration
# ---------------------------------------------------------------------------
@calls_bp.route("/api/push-subscribe", methods=["POST"])
def push_subscribe():
    data = request.get_json()
    if not data or "subscription" not in data:
        return jsonify({"error": "No subscription data"}), 400
    agent_name = data.get("agent_name", "")
    save_subscription(agent_name, data["subscription"])
    return jsonify({"ok": True})
