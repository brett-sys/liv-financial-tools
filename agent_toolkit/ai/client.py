"""Thin server-side wrapper around the Anthropic SDK.

Forces structured output via tool use instead of asking the model for JSON,
which eliminates parse errors. The API key stays server-side (env var
ANTHROPIC_API_KEY) and is never exposed to the browser.
"""

import os

# Model strings (confirm current values at https://docs.claude.com).
MODEL_OPUS = "claude-opus-4-7"            # heaviest reasoning
MODEL_SONNET = "claude-sonnet-4-6"        # the workhorse
MODEL_HAIKU = "claude-haiku-4-5-20251001"  # cheap + fast, high volume

DEFAULT_MODEL = MODEL_SONNET

# (value, label) pairs for UI dropdowns.
MODEL_CHOICES = [
    (MODEL_SONNET, "Sonnet 4.6 — balanced (recommended)"),
    (MODEL_OPUS, "Opus 4.7 — deepest reasoning"),
    (MODEL_HAIKU, "Haiku 4.5 — fastest & cheapest"),
]

VALID_MODELS = {MODEL_OPUS, MODEL_SONNET, MODEL_HAIKU}


class AIError(Exception):
    """Raised for any AI configuration or API failure, with a user-safe message."""


def is_configured() -> bool:
    """True if an API key is present so the UI can show a helpful banner."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env to enable the AI tools."
        )
    try:
        import anthropic
    except ImportError as exc:
        raise AIError(
            "The 'anthropic' package is not installed. Run: pip install anthropic"
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


def structured_call(
    *,
    system: str,
    user_content: str = "",
    tool_name: str,
    tool_description: str,
    input_schema: dict,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    messages: list | None = None,
) -> dict:
    """Call Claude and force exactly one tool call, returning the tool input dict.

    Pass either ``user_content`` (single user turn) or a full ``messages`` list
    (e.g. for multi-turn roleplay debriefs).
    """
    if model not in VALID_MODELS:
        model = DEFAULT_MODEL

    client = _client()
    if messages is None:
        messages = [{"role": "user", "content": user_content}]

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[{
                "name": tool_name,
                "description": tool_description,
                "input_schema": input_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
            messages=messages,
        )
    except AIError:
        raise
    except Exception as exc:  # network / API / auth errors
        raise AIError(f"Claude API error: {exc}") from exc

    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            return block.input

    raise AIError("Claude did not return the expected structured output. Try again.")
