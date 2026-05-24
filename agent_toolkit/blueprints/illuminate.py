"""Illuminate blueprint – the AI coaching suite.

Tool 1 (Presentation Review Bot) is live. The shared Operating Principles
config is edited here in Settings and injected into every tool's prompt.
"""

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify,
)

from ai.client import (
    structured_call, chat, is_configured, AIError,
    MODEL_CHOICES, DEFAULT_MODEL,
)
from ai.prompts import (
    REVIEW_TOOL, review_system_prompt, DEFAULT_OPERATING_PRINCIPLES,
    PERSONALITIES, DIFFICULTIES, PRODUCTS,
    roleplay_system_prompt, debrief_system_prompt, DEBRIEF_TOOL,
    personality_label, difficulty_label,
)
from models.ai_coach import (
    get_operating_principles, save_operating_principles, is_using_default_principles,
    save_review, get_reviews, get_review,
    save_debrief, get_debriefs, get_debrief,
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


# ---------------------------------------------------------------------------
# Tool 2 — AI Training Partner (roleplay prospect + debrief)
# ---------------------------------------------------------------------------
_MAX_MESSAGES = 60  # bound cost on very long practice sessions


def _sanitize_messages(raw) -> list:
    """Keep only well-formed user/assistant turns, trimmed to the last N."""
    messages = []
    if isinstance(raw, list):
        for m in raw:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            content = (m.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    return messages[-_MAX_MESSAGES:]


def _format_transcript(messages: list) -> str:
    lines = []
    for m in messages:
        who = "Agent" if m["role"] == "user" else "Prospect"
        lines.append(f"{who}: {m['content']}")
    return "\n".join(lines)


@illuminate_bp.route("/roleplay")
def roleplay():
    return render_template(
        "ai_roleplay.html",
        personalities=PERSONALITIES, difficulties=DIFFICULTIES, products=PRODUCTS,
        models=MODEL_CHOICES, default_model=DEFAULT_MODEL, configured=is_configured(),
    )


@illuminate_bp.route("/roleplay/turn", methods=["POST"])
def roleplay_turn():
    if not is_configured():
        return jsonify({"error": "AI is not configured. Add ANTHROPIC_API_KEY to your .env."}), 400

    data = request.get_json(silent=True) or {}
    messages = _sanitize_messages(data.get("messages"))
    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "Say something to the prospect first."}), 400

    system = roleplay_system_prompt(
        data.get("personality", ""), data.get("difficulty", ""),
        data.get("product", ""), data.get("scenario", ""),
    )
    try:
        reply = chat(system=system, messages=messages,
                     model=data.get("model", DEFAULT_MODEL), max_tokens=350)
    except AIError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify({"reply": reply})


@illuminate_bp.route("/roleplay/debrief", methods=["POST"])
def roleplay_debrief():
    if not is_configured():
        return jsonify({"error": "AI is not configured. Add ANTHROPIC_API_KEY to your .env."}), 400

    data = request.get_json(silent=True) or {}
    messages = _sanitize_messages(data.get("messages"))
    agent_turns = sum(1 for m in messages if m["role"] == "user")
    if agent_turns < 2:
        return jsonify({"error": "Practice a bit more before ending — there's not enough to coach yet."}), 400

    model = data.get("model", DEFAULT_MODEL)
    system = debrief_system_prompt(get_operating_principles())
    try:
        result = structured_call(
            system=system,
            user_content="PRACTICE CALL TRANSCRIPT:\n\n" + _format_transcript(messages),
            tool_name=DEBRIEF_TOOL["name"],
            tool_description=DEBRIEF_TOOL["description"],
            input_schema=DEBRIEF_TOOL["input_schema"],
            model=model,
        )
    except AIError as exc:
        return jsonify({"error": str(exc)}), 502

    debrief_id = save_debrief(
        _current_agent(),
        personality_label(data.get("personality", "")),
        difficulty_label(data.get("difficulty", "")),
        (data.get("product") or "—").strip() or "—",
        result, agent_turns, model,
    )
    return jsonify({"debrief_id": debrief_id, "redirect": url_for("illuminate.debrief_detail", debrief_id=debrief_id)})


@illuminate_bp.route("/roleplay/history")
def roleplay_history():
    mine_only = request.args.get("scope") != "team"
    agent = _current_agent() if mine_only else None
    return render_template(
        "ai_debrief_history.html",
        debriefs=get_debriefs(agent_name=agent), mine_only=mine_only,
    )


@illuminate_bp.route("/roleplay/debrief/<int:debrief_id>")
def debrief_detail(debrief_id):
    data = get_debrief(debrief_id)
    if not data:
        abort(404)
    return render_template("ai_debrief_detail.html", d=data)
