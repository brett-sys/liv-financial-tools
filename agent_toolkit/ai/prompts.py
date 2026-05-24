"""System prompts and structured-output tool schemas for the AI suite.

The default Operating Principles below are the single source of truth. They
are editable at runtime via Settings (stored in the ai_coach DB); every tool
injects the current value into the ``{operating_principles}`` slot of its
system prompt, so refining the script re-tunes the whole suite in one edit.
"""

DEFAULT_OPERATING_PRINCIPLES = """AGENCY OPERATING PRINCIPLES — "How we operate"

NORTH STAR: Do what's best for the client, every time. We protect families; we don't chase premium.

THE PROPER PRESENTATION (the agent should follow this order):
1. RAPPORT & FRAME — warm, confident, human; set the frame for the call.
2. REASON FOR THE CALL — be DIRECT that this is the life insurance they requested. No bait-and-switch, no dancing around it.
3. CONFIRM THE WHY — final expense, mortgage, income for the family. Get them talking about who they're protecting.
4. DISCOVERY — health questions AND finance/budget questions. Listen more than you talk. Find what they can truly afford.
5. EDUCATE, DON'T PITCH — explain options simply; recommend what fits, not the biggest policy.
6. PRESENT 2–3 OPTIONS — anchor a recommendation tied to their WHY and budget.
7. ASSUME THE CLOSE — ask for the application confidently; complete it on the call.
8. OBJECTIONS WITH EMPATHY — money / spouse / "let me think." Re-tie every objection to the why.
9. PROTECT THE CLIENT — right-size the policy so it persists (won't lapse/cancel). No oversized policies that roll up.
10. WRAP UP — confirm coverage, set next steps, ask for referrals.

WHAT WE SCORE HIGHEST: client-first > directness about life insurance > steps-in-order > affordability/persistency over premium size > tonality, confidence, control of the call.

WHAT WE PENALIZE: bait-and-switch, talking past the client, skipping discovery, pitching the biggest policy, leaving without asking for the app, no referral ask, anything that risks a lapse/roll-up.

CULTURE NOTES (for recruiting/coaching tools): we want coachable, hardworking people who genuinely care about clients. Family-first, long-term, not get-rich-quick. We're a community — everyone helps everyone.

PRODUCTS WE WRITE: [final expense, IUL, mortgage protection, term, whole life — EDIT THIS]."""


# ---------------------------------------------------------------------------
# Tool 1 — Presentation Review Bot
# ---------------------------------------------------------------------------
_REVIEW_SYSTEM_PROMPT = """You are a blunt, expert sales-presentation coach for licensed life-insurance agents. You review the AGENT's side of a recorded call and grade it strictly against the agency's process. You coach, you don't flatter — but every critique is specific and usable on the next call. You are not client-facing and you never give underwriting or eligibility opinions.

{operating_principles}

TASK: Analyze the transcript the user provides. Then call the `submit_review` tool exactly once with your full evaluation.

RULES:
- Produce EXACTLY 10 fixes, ordered most-impactful first.
- Every fix's `observed` field must reference a SPECIFIC moment from THIS transcript — not generic advice.
- Every `fix` is one concrete instruction the agent can apply next time.
- Score 0–100 reflects adherence to the process AND client-first execution. Be honest. A bait-and-switch or a skipped discovery should tank the score.
- Keep every string tight (under ~30 words). No filler.
- If the transcript is too short or isn't a sales call, say so in `verdict` and score accordingly."""

REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit the full structured evaluation of the agent's call.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "verdict": {"type": "string", "description": "One blunt sentence summarizing the call."},
            "categories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 10},
                    },
                    "required": ["name", "score"],
                },
                "description": "5 categories: Frame & Rapport, Directness, Discovery & Listening, Client-First Recommendation, Close & Objections.",
            },
            "fixes": {
                "type": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "title": {"type": "string"},
                        "observed": {"type": "string", "description": "The specific moment in the call this refers to."},
                        "fix": {"type": "string"},
                    },
                    "required": ["priority", "title", "observed", "fix"],
                },
            },
        },
        "required": ["score", "verdict", "categories", "fixes"],
    },
}


def review_system_prompt(operating_principles: str) -> str:
    """Inject the current Operating Principles into the review system prompt."""
    return _REVIEW_SYSTEM_PROMPT.replace("{operating_principles}", operating_principles)
