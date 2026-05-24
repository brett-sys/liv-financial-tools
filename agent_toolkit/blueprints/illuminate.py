"""Illuminate blueprint – the AI coaching suite.

Tool 1 (Presentation Review Bot) is live. The shared Operating Principles
config is edited here in Settings and injected into every tool's prompt.
"""

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for, abort,
)

from ai.client import (
    structured_call, is_configured, AIError,
    MODEL_CHOICES, DEFAULT_MODEL,
)
from ai.prompts import REVIEW_TOOL, review_system_prompt, DEFAULT_OPERATING_PRINCIPLES
from models.ai_coach import (
    get_operating_principles, save_operating_principles, is_using_default_principles,
    save_review, get_reviews, get_review,
)

illuminate_bp = Blueprint("illuminate", __name__)


def _current_agent() -> str:
    return request.cookies.get("agent_pref", "Brett")


# ---------------------------------------------------------------------------
# Suite hub
# ---------------------------------------------------------------------------
@illuminate_bp.route("/")
def menu():
    return render_template("illuminate_menu.html", configured=is_configured())


# ---------------------------------------------------------------------------
# Tool 1 — Presentation Review Bot
# ---------------------------------------------------------------------------
@illuminate_bp.route("/review", methods=["GET", "POST"])
def review():
    if request.method == "POST":
        transcript = request.form.get("transcript", "").strip()
        label = request.form.get("label", "").strip()
        model = request.form.get("model", DEFAULT_MODEL).strip()

        if len(transcript) < 40:
            flash("Paste a real call transcript (agent + client) to review.", "error")
            return redirect(url_for("illuminate.review"))

        if not is_configured():
            flash("AI is not configured. Add ANTHROPIC_API_KEY to your .env.", "error")
            return redirect(url_for("illuminate.review"))

        system = review_system_prompt(get_operating_principles())
        try:
            result = structured_call(
                system=system,
                user_content="CALL TRANSCRIPT:\n\n" + transcript,
                tool_name=REVIEW_TOOL["name"],
                tool_description=REVIEW_TOOL["description"],
                input_schema=REVIEW_TOOL["input_schema"],
                model=model,
            )
        except AIError as exc:
            flash(str(exc), "error")
            return redirect(url_for("illuminate.review"))

        review_id = save_review(_current_agent(), label, result, model)
        return render_template(
            "ai_review.html",
            result=result, label=label, model=model, review_id=review_id,
            models=MODEL_CHOICES, default_model=DEFAULT_MODEL, configured=True,
        )

    return render_template(
        "ai_review.html",
        result=None, models=MODEL_CHOICES, default_model=DEFAULT_MODEL,
        configured=is_configured(),
    )


@illuminate_bp.route("/review/history")
def review_history():
    mine_only = request.args.get("scope") != "team"
    agent = _current_agent() if mine_only else None
    reviews = get_reviews(agent_name=agent)
    return render_template(
        "ai_review_history.html",
        reviews=reviews, mine_only=mine_only, agent=_current_agent(),
    )


@illuminate_bp.route("/review/<int:review_id>")
def review_detail(review_id):
    data = get_review(review_id)
    if not data:
        abort(404)
    return render_template("ai_review_detail.html", r=data)


# ---------------------------------------------------------------------------
# Settings — the shared Operating Principles config
# ---------------------------------------------------------------------------
@illuminate_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        text = request.form.get("operating_principles", "").strip()
        if not text:
            flash("Operating Principles can't be empty.", "error")
            return redirect(url_for("illuminate.settings"))
        save_operating_principles(text)
        flash("Operating Principles saved. Every AI tool now uses the new version.", "success")
        return redirect(url_for("illuminate.settings"))

    return render_template(
        "ai_settings.html",
        principles=get_operating_principles(),
        default_text=DEFAULT_OPERATING_PRINCIPLES,
        using_default=is_using_default_principles(),
        configured=is_configured(),
    )
