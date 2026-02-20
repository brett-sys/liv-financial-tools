"""Tools blueprint – Illustration, Illustration Comparison, Policy Submitted, Quote Comparison."""

import json
import tempfile
from pathlib import Path

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    send_file,
)

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
                    "rating": request.form.get(f"rating_{i}", "").strip() or "—",
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
