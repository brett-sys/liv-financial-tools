"""Lead Manager – Pull CSV leads from Google Drive → Import into Go High Level."""

import time

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session,
)

import config
import drive
import ghl

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ---------------------------------------------------------------------------
# Routes – File Browser (home page)
# ---------------------------------------------------------------------------

@app.route("/")
def files():
    """List all CSV files in the Google Drive folder."""
    try:
        csv_files = drive.list_csv_files()
    except Exception as e:
        csv_files = []
        flash(f"Could not load Drive folder: {e}", "error")

    ghl_ok = ghl.check_config() is None
    agents = config.load_agents()

    return render_template(
        "files.html",
        files=csv_files,
        total=len(csv_files),
        ghl_ok=ghl_ok,
        agents=agents,
    )


# ---------------------------------------------------------------------------
# Routes – View Leads in a CSV
# ---------------------------------------------------------------------------

@app.route("/leads/<file_id>")
def view_leads(file_id):
    """Download and display leads from a specific CSV file."""
    try:
        csv_files = drive.list_csv_files()
        file_info = next((f for f in csv_files if f["id"] == file_id), None)
        leads = drive.download_csv(file_id)
    except Exception as e:
        flash(f"Could not load file: {e}", "error")
        return redirect(url_for("files"))

    search = request.args.get("search", "").lower()
    if search:
        leads = [
            l for l in leads
            if search in l.get("full_name", "").lower()
            or search in l.get("phone", "")
            or search in l.get("city", "").lower()
        ]

    agents = config.load_agents()
    ghl_ok = ghl.check_config() is None
    file_name = file_info["name"] if file_info else file_id

    return render_template(
        "leads.html",
        leads=leads,
        total=len(leads),
        file_id=file_id,
        file_name=file_name,
        agents=agents,
        ghl_ok=ghl_ok,
        search=request.args.get("search", ""),
    )


# ---------------------------------------------------------------------------
# Routes – Import to GHL
# ---------------------------------------------------------------------------

@app.route("/import", methods=["POST"])
def import_leads():
    """Import selected leads from a CSV into GHL with agent tag."""
    file_id = request.form.get("file_id", "")
    agent_name = request.form.get("agent_name", "")
    selected = request.form.getlist("selected")
    extra_tags = [t.strip() for t in request.form.get("extra_tags", "").split(",") if t.strip()]

    if not agent_name:
        flash("Pick an agent first.", "error")
        return redirect(url_for("view_leads", file_id=file_id))

    if not selected:
        flash("Select at least one lead.", "error")
        return redirect(url_for("view_leads", file_id=file_id))

    try:
        leads = drive.download_csv(file_id)
    except Exception as e:
        flash(f"Could not load file: {e}", "error")
        return redirect(url_for("files"))

    selected_indices = set(int(s) for s in selected)

    imported = 0
    failed = 0
    for lead in leads:
        if lead["_index"] not in selected_indices:
            continue
        result = ghl.import_lead(lead, agent_name, extra_tags=extra_tags or None)
        if result["success"]:
            imported += 1
        else:
            failed += 1
        time.sleep(0.15)  # rate-limit GHL API calls

    msg = f"Imported {imported} lead(s) to Elite 360 → tagged '{agent_name}'"
    if extra_tags:
        msg += f" + {extra_tags}"
    if failed:
        msg += f" ({failed} failed)"
    flash(msg, "success" if imported else "error")
    return redirect(url_for("view_leads", file_id=file_id))


# ---------------------------------------------------------------------------
# Routes – Agent Config
# ---------------------------------------------------------------------------

@app.route("/agents")
def agents_page():
    agents = config.load_agents()
    return render_template("agents.html", agents=agents)


@app.route("/agents/add", methods=["POST"])
def add_agent():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("agents_page"))

    agents = config.load_agents()
    if any(a["name"] == name for a in agents):
        flash(f"Agent '{name}' already exists.", "error")
        return redirect(url_for("agents_page"))

    agents.append({"name": name, "email": email})
    config.save_agents(agents)
    flash(f"Added {name}.", "success")
    return redirect(url_for("agents_page"))


@app.route("/agents/remove", methods=["POST"])
def remove_agent():
    name = request.form.get("name", "")
    agents = config.load_agents()
    agents = [a for a in agents if a["name"] != name]
    config.save_agents(agents)
    flash(f"Removed {name}.", "success")
    return redirect(url_for("agents_page"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"\n  Lead Manager running at: http://localhost:{config.PORT}\n")
    app.run(host=config.HOST, port=config.PORT, debug=True)
