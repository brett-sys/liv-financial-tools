"""Call Logger – Flask web application."""

from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    make_response,
)

import config
import models
from sheets import export_week_to_sheets
from calendar_integration import get_calendar_urls, generate_ics

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ---------------------------------------------------------------------------
# Initialise DB and background scheduler
# ---------------------------------------------------------------------------
with app.app_context():
    models.init_db()

import scheduler  # noqa: F401 — starts APScheduler for weekly Sheets export


# ---------------------------------------------------------------------------
# Theme: set via /kevin or /brett URL, stored in cookie
# ---------------------------------------------------------------------------
@app.route("/kevin")
def set_kevin_theme():
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("theme", "kevin", max_age=60*60*24*365)
    resp.set_cookie("agent_pref", "Kevin Nelson", max_age=60*60*24*365)
    return resp


@app.route("/brett")
def set_brett_theme():
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("theme", "brett", max_age=60*60*24*365)
    resp.set_cookie("agent_pref", "Brett", max_age=60*60*24*365)
    return resp


@app.route("/easton")
def set_easton_theme():
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("theme", "easton", max_age=60*60*24*365)
    resp.set_cookie("agent_pref", "Easton Passolt", max_age=60*60*24*365)
    return resp


@app.route("/joe")
def set_joe_theme():
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("theme", "joe", max_age=60*60*24*365)
    resp.set_cookie("agent_pref", "Joe", max_age=60*60*24*365)
    return resp


@app.context_processor
def inject_theme():
    """Make theme and agent_pref available in all templates."""
    # Cookie override if set, otherwise detect from hostname
    cookie_theme = request.cookies.get("theme")
    if cookie_theme:
        theme = cookie_theme
        agent_pref = request.cookies.get("agent_pref", "Brett")
    else:
        host = request.host.split(":")[0]
        is_local = host in ("localhost", "127.0.0.1") or host.startswith("192.168.")
        theme = "brett" if is_local else "kevin"
        agent_pref = "Brett" if is_local else "Kevin Nelson"
    return {"theme": theme, "agent_pref": agent_pref}


# ---------------------------------------------------------------------------
# Dashboard / home
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    stats = models.get_stats()
    return render_template("index.html", stats=stats, now=datetime.now())


# ---------------------------------------------------------------------------
# Log a new call
# ---------------------------------------------------------------------------
@app.route("/log", methods=["GET", "POST"])
def log_call():
    if request.method == "POST":
        models.log_call(
            agent_name=request.form.get("agent_name", "").strip(),
            contact_name=request.form.get("contact_name", "").strip(),
            phone_number=request.form.get("phone_number", "").strip(),
            call_datetime=request.form.get("call_datetime",
                                           datetime.now().strftime("%Y-%m-%d %H:%M")),
            direction=request.form.get("direction", "Outbound"),
            outcome=request.form.get("outcome", "Other"),
            notes=request.form.get("notes", "").strip(),
            follow_up_date=request.form.get("follow_up_date") or None,
        )
        follow_up = request.form.get("follow_up_date")
        agent = request.form.get("agent_name", "").strip()
        if follow_up:
            cal = get_calendar_urls(
                agent_name=agent,
                contact_name=request.form.get("contact_name", "").strip(),
                phone_number=request.form.get("phone_number", "").strip(),
                follow_up_date=follow_up,
                notes=request.form.get("notes", "").strip(),
            )
            flash("Call logged!", "success")
            return render_template("cal_redirect.html", cal=cal)
        else:
            flash("Call logged successfully!", "success")
        return redirect(url_for("index"))

    return render_template(
        "log.html",
        directions=config.DIRECTION_CHOICES,
        outcomes=config.OUTCOME_CHOICES,
        agents=config.AGENT_CHOICES,
        now=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Edit an existing call
# ---------------------------------------------------------------------------
@app.route("/edit/<int:call_id>", methods=["GET", "POST"])
def edit_call(call_id):
    call = models.get_call(call_id)
    if not call:
        flash("Call not found.", "error")
        return redirect(url_for("history"))

    if request.method == "POST":
        models.update_call(
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
        return redirect(url_for("history"))

    return render_template(
        "edit.html",
        call=call,
        directions=config.DIRECTION_CHOICES,
        outcomes=config.OUTCOME_CHOICES,
        agents=config.AGENT_CHOICES,
    )


# ---------------------------------------------------------------------------
# Delete a call
# ---------------------------------------------------------------------------
@app.route("/delete/<int:call_id>", methods=["POST"])
def delete_call(call_id):
    models.delete_call(call_id)
    flash("Call deleted.", "success")
    return redirect(url_for("history"))


# ---------------------------------------------------------------------------
# Call history with filters
# ---------------------------------------------------------------------------
@app.route("/history")
def history():
    agent_name = request.args.get("agent_name", "")
    direction = request.args.get("direction", "")
    outcome = request.args.get("outcome", "")
    search = request.args.get("search", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    calls = models.get_calls(
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
        agents=config.AGENT_CHOICES,
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
# API: contact auto-suggest
# ---------------------------------------------------------------------------
@app.route("/api/suggest")
def suggest():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    return jsonify(models.get_contact_suggestions(q))


# ---------------------------------------------------------------------------
# Manual export to Google Sheets
# ---------------------------------------------------------------------------
@app.route("/export", methods=["POST"])
def export_now():
    try:
        result = export_week_to_sheets()
        flash(f"Exported to Google Sheets: {result}", "success")
    except Exception as e:
        flash(f"Export failed: {e}", "error")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Calendar .ics download
# ---------------------------------------------------------------------------
@app.route("/calendar.ics")
def download_ics():
    contact = request.args.get("contact", "")
    phone = request.args.get("phone", "")
    date = request.args.get("date", "")
    notes = request.args.get("notes", "")
    if not date:
        flash("No follow-up date provided.", "error")
        return redirect(url_for("index"))
    ics_content = generate_ics(contact, phone, date, notes)
    resp = make_response(ics_content)
    resp.headers["Content-Type"] = "text/calendar; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=follow_up.ics"
    return resp


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=True)
