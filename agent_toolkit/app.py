"""LIFI Agent Toolkit – main Flask application."""

from flask import Flask, request, make_response, redirect, url_for

import config
from models.calls import init_db
from models.scoreboard import init_db as init_scoreboard_db
from models.ai_coach import init_db as init_ai_coach_db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with app.app_context():
    init_db()
    init_scoreboard_db()
    init_ai_coach_db()

# ---------------------------------------------------------------------------
# Register blueprints
# ---------------------------------------------------------------------------
from blueprints.calls import calls_bp               # noqa: E402
from blueprints.quoter import quoter_bp             # noqa: E402
from blueprints.tools import tools_bp               # noqa: E402
from blueprints.referrals import referrals_bp       # noqa: E402
from blueprints.underwriting_api import underwriting_bp  # noqa: E402
from blueprints.scoreboard import scoreboard_bp     # noqa: E402
from blueprints.illuminate import illuminate_bp     # noqa: E402

app.register_blueprint(calls_bp)
app.register_blueprint(quoter_bp, url_prefix="/quoter")
app.register_blueprint(tools_bp, url_prefix="/tools")
app.register_blueprint(referrals_bp, url_prefix="/referrals")
app.register_blueprint(underwriting_bp, url_prefix="/underwriting")
app.register_blueprint(scoreboard_bp)
app.register_blueprint(illuminate_bp, url_prefix="/illuminate")


# ---------------------------------------------------------------------------
# Theme: set via /<agent_slug>, detected by hostname, stored in cookie
# ---------------------------------------------------------------------------
THEME_ROUTES = {}
# Primary slug: full agent name, lowercased, no spaces (e.g. "Kevin Nelson" -> kevinnelson).
for agent in config.AGENTS:
    slug = agent["name"].lower().replace(" ", "")
    THEME_ROUTES[slug] = agent
# Alias: theme key for short links (e.g. /kevin) when it does not collide with another name slug.
for agent in config.AGENTS:
    theme_slug = (agent.get("theme") or "").strip().lower()
    if theme_slug and theme_slug not in THEME_ROUTES:
        THEME_ROUTES[theme_slug] = agent


@app.route("/<slug>")
def set_agent_theme(slug):
    agent = THEME_ROUTES.get(slug)
    if not agent:
        return redirect(url_for("calls.leaderboard"))
    resp = make_response(redirect(url_for("calls.leaderboard")))
    resp.set_cookie("theme", agent["theme"], max_age=60 * 60 * 24 * 365)
    resp.set_cookie("agent_pref", agent["name"], max_age=60 * 60 * 24 * 365)
    return resp


@app.context_processor
def inject_globals():
    cookie_theme = request.cookies.get("theme")
    if cookie_theme:
        theme = cookie_theme
        agent_pref = request.cookies.get("agent_pref", "Brett")
    else:
        # First visit (no cookies): use first agent in config — not a hardcoded production default.
        first = config.AGENTS[0] if config.AGENTS else {"name": "Brett", "theme": "brett"}
        theme = first["theme"]
        agent_pref = first["name"]
    return {
        "theme": theme,
        "agent_pref": agent_pref,
        "agents": config.AGENT_CHOICES,
        "app_name": "LIFI",
        "vapid_public_key": config.VAPID_PUBLIC_KEY,
        "social_links": config.SOCIAL_LINKS,
        "app_store_url": config.APP_STORE_URL,
        "play_store_url": config.PLAY_STORE_URL,
    }


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("calls.leaderboard"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import scheduler  # noqa: F401
    app.run(host=config.HOST, port=config.PORT, debug=True)
