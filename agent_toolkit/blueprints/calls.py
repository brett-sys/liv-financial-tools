"""Calls blueprint – leaderboard, call logging, history, GHL sync."""

import threading
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    make_response,
)

import config
from models.calls import (
    log_call as db_log_call, update_call, delete_call, get_call,
    get_calls, get_stats, get_contact_suggestions, get_follow_up_dates,
)
from calendar_integration import get_calendar_urls, generate_ics
import ghl_integration
from ghl_integration import upsert_contact, GHLError
from push import save_subscription

calls_bp = Blueprint("calls", __name__)


# ---------------------------------------------------------------------------
# Leaderboard / Dashboard
# ---------------------------------------------------------------------------
@calls_bp.route("/dashboard")
def leaderboard():
    agent_pref = request.cookies.get("agent_pref", "Brett")
    stats = get_stats(agent_name=agent_pref)
    follow_up_dates = get_follow_up_dates(agent_pref)
    return render_template(
        "leaderboard.html",
        stats=stats,
        now=datetime.now(),
        follow_up_dates=follow_up_dates,
        calendar_id=config.AGENT_CALENDAR_IDS.get(agent_pref, ""),
        calendar_type=config.AGENT_CALENDAR_TYPES.get(agent_pref, "google"),
        social_links=config.SOCIAL_LINKS,
        app_store_url=config.APP_STORE_URL,
        play_store_url=config.PLAY_STORE_URL,
    )


# ---------------------------------------------------------------------------
# Log a new call
# ---------------------------------------------------------------------------
@calls_bp.route("/log", methods=["GET", "POST"])
def log_call_route():
    if request.method == "POST":
        agent = request.form.get("agent_name", "").strip()
        contact = request.form.get("contact_name", "").strip()
        phone = request.form.get("phone_number", "").strip()
        agent = request.cookies.get("agent_pref", agent) or agent

        outcome = request.form.get("outcome", "Other")

        db_log_call(
            agent_name=agent,
            contact_name=contact,
            phone_number=phone,
            call_datetime=request.form.get(
                "call_datetime", datetime.now().strftime("%Y-%m-%d %H:%M")
            ),
            direction=request.form.get("direction", "Outbound"),
            outcome=outcome,
            notes=request.form.get("notes", "").strip(),
            follow_up_date=request.form.get("follow_up_date") or None,
        )

        if config.GHL_ENABLED and outcome in config.GHL_STAGE_MAP:
            def _ghl_pipeline_sync():
                try:
                    contact_id = ghl_integration.upsert_contact(
                        name=contact, phone=phone,
                    )
                    stage_id = config.GHL_STAGE_MAP.get(outcome)
                    if stage_id and config.GHL_PIPELINE_ID:
                        ghl_integration.upsert_opportunity(
                            contact_id=contact_id,
                            pipeline_id=config.GHL_PIPELINE_ID,
                            stage_id=stage_id,
                            name=f"{contact} — {outcome}",
                        )
                except Exception as e:
                    print(f"[GHL] Background pipeline sync failed: {e}")

            t = threading.Thread(target=_ghl_pipeline_sync, daemon=True)
            t.start()

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
    agent_pref = request.cookies.get("agent_pref", "Brett")
    direction = request.args.get("direction", "")
    outcome = request.args.get("outcome", "")
    search = request.args.get("search", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    calls = get_calls(
        agent_name=agent_pref,
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
            "agent_name": agent_pref,
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
