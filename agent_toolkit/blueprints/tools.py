"""Tools blueprint – Illustration, Comparison, Policy Submitted, Quote Comparison, Pipeline, Quick Quote, Teleprompter."""

import json
import tempfile
from pathlib import Path

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    send_file, jsonify,
)

import config
from models.calls import get_pipeline_data

tools_bp = Blueprint("tools", __name__)


def _get_pdf_engine():
    """Lazy import the pdf engine modules."""
    from pdf_engine.parsers import (
        parse_data_to_html, parse_graph_points, parse_summary_data,
        parse_policy_submitted_email, ParseError,
    )
    from pdf_engine.html_builders import (
        generate_pdf_html, build_policy_submitted_html,
        build_quote_comparison_html,
    )
    from pdf_engine.pdf_gen import generate_pdf_bytes
    from pdf_engine.assets import (
        load_logo_data_uri, load_nlg_logo_data_uri,
        load_agent_photo_data_uri,
    )
    return {
        "parse_data_to_html": parse_data_to_html,
        "parse_graph_points": parse_graph_points,
        "parse_summary_data": parse_summary_data,
        "parse_policy_submitted_email": parse_policy_submitted_email,
        "ParseError": ParseError,
        "generate_pdf_html": generate_pdf_html,
        "build_policy_submitted_html": build_policy_submitted_html,
        "build_quote_comparison_html": build_quote_comparison_html,
        "generate_pdf_bytes": generate_pdf_bytes,
        "load_logo_data_uri": load_logo_data_uri,
        "load_nlg_logo_data_uri": load_nlg_logo_data_uri,
        "load_agent_photo_data_uri": load_agent_photo_data_uri,
    }


# ---------------------------------------------------------------------------
# Tools menu
# ---------------------------------------------------------------------------
@tools_bp.route("/")
def tools_menu():
    return render_template("tools_menu.html")


# ---------------------------------------------------------------------------
# IUL Illustration
# ---------------------------------------------------------------------------
@tools_bp.route("/illustration", methods=["GET", "POST"])
def illustration():
    if request.method == "POST":
        data = request.form.get("paste_data", "").strip()
        client_name = request.form.get("client_name", "").strip()
        if not data:
            flash("Please paste illustration data.", "error")
            return redirect(url_for("tools.illustration"))

        try:
            eng = _get_pdf_engine()
            html_body = eng["parse_data_to_html"](data)
            graph_points = eng["parse_graph_points"](data)
            summary_data = eng["parse_summary_data"](data)
            logo = eng["load_logo_data_uri"]()
            nlg_logo = eng["load_nlg_logo_data_uri"]()
            agent_photo = eng["load_agent_photo_data_uri"]()

            html_content = eng["generate_pdf_html"](
                html_body,
                logo_data_uri=logo,
                graph_points=graph_points,
                summary_data=summary_data,
                nlg_logo_data_uri=nlg_logo,
                agent_photo_data_uri=agent_photo,
                client_name=client_name,
            )

            pdf_bytes = eng["generate_pdf_bytes"](html_content)
            filename = f"{client_name or 'illustration'}_IUL.pdf".replace(" ", "_")

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()

            return send_file(
                tmp.name,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename,
            )
        except Exception as e:
            flash(f"PDF generation failed: {e}", "error")
            return redirect(url_for("tools.illustration"))

    return render_template("illustration.html")


# ---------------------------------------------------------------------------
# Illustration Comparison
# ---------------------------------------------------------------------------
@tools_bp.route("/comparison", methods=["GET", "POST"])
def illustration_comparison():
    if request.method == "POST":
        client_name = request.form.get("client_name", "").strip()
        policies = []
        for i in range(1, 5):
            label = request.form.get(f"label_{i}", f"Policy {i}").strip()
            data = request.form.get(f"paste_{i}", "").strip()
            if data:
                policies.append({"label": label, "data": data})

        if len(policies) < 2:
            flash("Paste data for at least 2 policies to compare.", "error")
            return redirect(url_for("tools.illustration_comparison"))

        try:
            eng = _get_pdf_engine()
            parsed = []
            for p in policies:
                summary = eng["parse_summary_data"](p["data"])
                graph = eng["parse_graph_points"](p["data"])
                parsed.append({
                    "label": p["label"],
                    "summary": summary,
                    "graph": graph,
                })

            from pdf_engine.comparison_builder import build_comparison_html
            logo = eng["load_logo_data_uri"]()
            agent_photo = eng["load_agent_photo_data_uri"]()

            html_content = build_comparison_html(
                client_name=client_name,
                policies=parsed,
                logo_data_uri=logo,
                agent_photo_data_uri=agent_photo,
            )

            pdf_bytes = eng["generate_pdf_bytes"](html_content)
            filename = f"{client_name or 'comparison'}_comparison.pdf".replace(" ", "_")

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()

            return send_file(
                tmp.name, mimetype="application/pdf",
                as_attachment=True, download_name=filename,
            )
        except Exception as e:
            flash(f"Comparison PDF failed: {e}", "error")
            return redirect(url_for("tools.illustration_comparison"))

    return render_template("illus_comparison.html")


# ---------------------------------------------------------------------------
# Policy Submitted
# ---------------------------------------------------------------------------
@tools_bp.route("/policy-submitted", methods=["GET", "POST"])
def policy_submitted():
    if request.method == "POST":
        data = request.form.get("paste_data", "").strip()
        if not data:
            flash("Please paste policy confirmation data.", "error")
            return redirect(url_for("tools.policy_submitted"))

        try:
            eng = _get_pdf_engine()

            payload = eng["parse_policy_submitted_email"](data)
            if payload is None:
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    flash("Could not parse policy details. Paste the confirmation email text.", "error")
                    return redirect(url_for("tools.policy_submitted"))

            logo = eng["load_logo_data_uri"]()
            html_content = eng["build_policy_submitted_html"](payload, logo)
            pdf_bytes = eng["generate_pdf_bytes"](html_content)

            client_name = payload.get("client_name", "policy")
            filename = f"{client_name}_policy_submitted.pdf".replace(" ", "_")

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()

            return send_file(
                tmp.name, mimetype="application/pdf",
                as_attachment=True, download_name=filename,
            )
        except Exception as e:
            flash(f"PDF generation failed: {e}", "error")
            return redirect(url_for("tools.policy_submitted"))

    return render_template("policy_submitted.html")


# ---------------------------------------------------------------------------
# Quote Comparison
# ---------------------------------------------------------------------------
@tools_bp.route("/quote-comparison", methods=["GET", "POST"])
def quote_comparison():
    if request.method == "POST":
        client_name = request.form.get("client_name", "").strip()
        client_age = request.form.get("client_age", "").strip()
        recommended = request.form.get("recommended", "1").strip()

        carriers = []
        for i in range(1, 5):
            carrier = request.form.get(f"carrier_{i}", "").strip()
            if carrier:
                carriers.append({
                    "carrier": carrier,
                    "product": request.form.get(f"product_{i}", "").strip() or "—",
                    "monthly_premium": request.form.get(f"premium_{i}", "").strip() or "—",
                    "death_benefit": request.form.get(f"death_benefit_{i}", "").strip() or "—",
                    "cash_value_10yr": request.form.get(f"cash_value_{i}", "").strip() or "—",
                    "cash_value_20yr": request.form.get(f"cash_value_20yr_{i}", "").strip() or "—",
                    "am_best": request.form.get(f"am_best_{i}", "").strip() or "",
                    "sp": request.form.get(f"sp_{i}", "").strip() or "",
                    "moodys": request.form.get(f"moodys_{i}", "").strip() or "",
                    "about": request.form.get(f"about_{i}", "").strip() or "",
                })

        if not client_name or not carriers:
            flash("Enter client name and at least one carrier.", "error")
            return redirect(url_for("tools.quote_comparison"))

        recommended_idx = None
        try:
            rec = int(recommended)
            if 1 <= rec <= len(carriers):
                recommended_idx = rec - 1
        except (ValueError, TypeError):
            pass

        try:
            eng = _get_pdf_engine()
            logo = eng["load_logo_data_uri"]()
            agent_photo = eng["load_agent_photo_data_uri"]()

            html_content = eng["build_quote_comparison_html"](
                client_name=client_name,
                client_age=client_age,
                carriers=carriers,
                recommended_idx=recommended_idx,
                logo_data_uri=logo,
                agent_photo_data_uri=agent_photo,
            )

            pdf_bytes = eng["generate_pdf_bytes"](html_content)
            filename = f"{client_name}_quote_comparison.pdf".replace(" ", "_")

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()

            return send_file(
                tmp.name, mimetype="application/pdf",
                as_attachment=True, download_name=filename,
            )
        except Exception as e:
            flash(f"PDF generation failed: {e}", "error")
            return redirect(url_for("tools.quote_comparison"))

    return render_template("quote_comparison.html")


# ---------------------------------------------------------------------------
# JSON API – Generate Illustration PDF & Email to Client
# ---------------------------------------------------------------------------
@tools_bp.route("/api/illustration", methods=["POST"])
def api_illustration():
    """Accept JSON, generate an IUL illustration PDF, and email it to the client.

    Expects JSON body:
        paste_data   (str, required) – raw carrier illustration text
        client_name  (str, required) – client's full name
        client_email (str, required) – client's email address

    Returns JSON with success status and message.
    """
    payload = request.get_json(silent=True) or {}
    paste_data = (payload.get("paste_data") or "").strip()
    client_name = (payload.get("client_name") or "").strip()
    client_email = (payload.get("client_email") or "").strip()

    errors = []
    if not paste_data:
        errors.append("paste_data is required")
    if not client_name:
        errors.append("client_name is required")
    if not client_email:
        errors.append("client_email is required")
    if errors:
        return jsonify({"success": False, "error": ", ".join(errors)}), 400

    try:
        eng = _get_pdf_engine()
        html_body = eng["parse_data_to_html"](paste_data)
        graph_points = eng["parse_graph_points"](paste_data)
        summary_data = eng["parse_summary_data"](paste_data)
        logo = eng["load_logo_data_uri"]()
        nlg_logo = eng["load_nlg_logo_data_uri"]()
        agent_photo = eng["load_agent_photo_data_uri"]()

        html_content = eng["generate_pdf_html"](
            html_body,
            logo_data_uri=logo,
            graph_points=graph_points,
            summary_data=summary_data,
            nlg_logo_data_uri=nlg_logo,
            agent_photo_data_uri=agent_photo,
            client_name=client_name,
        )

        pdf_bytes = eng["generate_pdf_bytes"](html_content)
        filename = f"{client_name or 'illustration'}_IUL.pdf".replace(" ", "_")
    except Exception as e:
        return jsonify({"success": False, "error": f"PDF generation failed: {e}"}), 500

    from email_utils import send_illustration_email, EmailError

    try:
        send_illustration_email(client_name, client_email, pdf_bytes, filename)
    except EmailError as e:
        return jsonify({
            "success": False,
            "error": f"PDF was generated but email failed: {e}",
            "pdf_generated": True,
        }), 500

    return jsonify({
        "success": True,
        "message": f"Illustration PDF emailed to {client_email}",
        "filename": filename,
    })


# ---------------------------------------------------------------------------
# Pipeline (Kanban Board)
# ---------------------------------------------------------------------------
@tools_bp.route("/pipeline")
def pipeline():
    pipeline_data = get_pipeline_data()
    stages = config.OUTCOME_CHOICES
    return render_template("pipeline.html", pipeline_data=pipeline_data, stages=stages)


# ---------------------------------------------------------------------------
# Quick Quote (IUL Calculator)
# ---------------------------------------------------------------------------
@tools_bp.route("/quick-quote")
def quick_quote():
    return render_template("quick_quote.html")


# ---------------------------------------------------------------------------
# Teleprompter
# ---------------------------------------------------------------------------
@tools_bp.route("/teleprompter")
def teleprompter():
    scripts = _load_scripts()
    return render_template("teleprompter.html", scripts=scripts)


def _load_scripts():
    """Load call scripts from the scripts directory."""
    scripts = []
    scripts_dir = config.SCRIPTS_DIR
    if not scripts_dir.exists():
        scripts_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(scripts_dir.glob("*.html")):
        scripts.append({"name": f.stem.replace("_", " ").title(), "content": f.read_text()})
    if not scripts:
        scripts.append({
            "name": "Cold Call Intro",
            "content": _default_cold_call_script(),
        })
    return scripts


def _default_cold_call_script():
    return """<p><strong>Opening:</strong></p>
<p>Hi, this is [Your Name] with LIV Financial Group. I'm reaching out because I help families like yours protect their financial future with tax-advantaged life insurance strategies.</p>

<p><strong>Permission:</strong></p>
<p>Do you have just 2 minutes? I won't take much of your time.</p>

<p><strong>Discovery:</strong></p>
<p>Quick question — do you currently have any life insurance in place?</p>
<p><em>If yes:</em> Great! Is it through your employer or a personal policy?</p>
<p><em>If no:</em> That's actually very common. Most people know they need it but haven't gotten around to it yet.</p>

<p><strong>Value Prop:</strong></p>
<p>What makes what we do different is we focus on <strong>Indexed Universal Life</strong> policies that not only provide a death benefit for your family, but also build <strong>tax-free cash value</strong> you can access during your lifetime — for retirement, emergencies, or opportunities.</p>

<p><strong>Close for Appointment:</strong></p>
<p>I'd love to run a quick illustration for you — it takes about 15 minutes and there's zero obligation. Would tomorrow at [time] work, or is [alternative time] better?</p>

<p data-objection="too-expensive"><strong>Objection — "Too Expensive":</strong></p>
<p>I totally understand that concern. The good news is we can design a policy that fits your budget — even starting at $100-200/month. And unlike term insurance that expires worthless, every dollar builds real cash value. Would it help if I showed you what $150/month could grow to over 20 years?</p>

<p data-objection="need-to-think"><strong>Objection — "Need to Think About It":</strong></p>
<p>Absolutely, this is an important decision. What specifically would you want to think over? I ask because sometimes I can answer those questions right now and save you some time.</p>

<p data-objection="already-have-coverage"><strong>Objection — "Already Have Coverage":</strong></p>
<p>That's great that you're already protected! Most of my clients actually had some coverage already — what we found is their employer policy wouldn't be enough for their family, or they were missing the wealth-building component. Would it be worth 15 minutes to see if there's a gap?</p>

<p data-objection="not-interested"><strong>Objection — "Not Interested":</strong></p>
<p>I respect that. Quick question before I go — is it the timing, or is life insurance in general not a priority right now? I ask because a lot of folks say the same thing, and then when I show them the tax-free retirement angle, they realize it's more than just a death benefit.</p>

<p data-objection="talk-to-spouse"><strong>Objection — "Need to Talk to My Spouse":</strong></p>
<p>That makes total sense — it's a decision you should absolutely make together. What if we set up a quick call with both of you? That way you're both hearing the same information and can make a decision together. Would an evening call this week work?</p>"""
