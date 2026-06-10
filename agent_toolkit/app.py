"""LIFI Agent Toolkit – Quoter + Scoreboard."""

from flask import Flask, request, make_response, redirect, url_for

import config
from models.scoreboard import init_db as init_scoreboard_db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with app.app_context():
    init_scoreboard_db()

# ---------------------------------------------------------------------------
# Register blueprints (quoter + scoreboard only)
# ---------------------------------------------------------------------------
from blueprints.quoter import quoter_bp             # noqa: E402
from blueprints.scoreboard import scoreboard_bp     # noqa: E402

app.register_blueprint(quoter_bp, url_prefix="/quoter")
app.register_blueprint(scoreboard_bp)


# ---------------------------------------------------------------------------
# Theme: set via /<agent_slug>, stored in cookie
# ---------------------------------------------------------------------------
THEME_ROUTES = {}
for agent in config.AGENTS:
    slug = agent["name"].lower().replace(" ", "")
    THEME_ROUTES[slug] = agent
for agent in config.AGENTS:
    theme_slug = (agent.get("theme") or "").strip().lower()
    if theme_slug and theme_slug not in THEME_ROUTES:
        THEME_ROUTES[theme_slug] = agent

RESERVED_SLUGS = {"quoter", "scoreboard", "static", "favicon.ico"}


@app.route("/<slug>")
def set_agent_theme(slug):
    if slug in RESERVED_SLUGS:
        return redirect(url_for("quoter.quoter_page"))
    agent = THEME_ROUTES.get(slug)
    if not agent:
        return redirect(url_for("quoter.quoter_page"))
    resp = make_response(redirect(url_for("quoter.quoter_page")))
    resp.set_cookie("theme", agent["theme"], max_age=60 * 60 * 24 * 365)
    resp.set_cookie("agent_pref", agent["name"], max_age=60 * 60 * 24 * 365)
    return resp


@app.context_processor
def inject_globals():
    first = config.AGENTS[0] if config.AGENTS else {"name": "Easton", "theme": "easton"}
    cookie_theme = request.cookies.get("theme")
    agent_pref = request.cookies.get("agent_pref", first["name"])
    valid_themes = {agent["theme"] for agent in config.AGENTS}
    if cookie_theme in valid_themes and agent_pref in config.AGENT_CHOICES:
        theme = cookie_theme
    else:
        theme = first["theme"]
        agent_pref = first["name"]
    return {
        "theme": theme,
        "agent_pref": agent_pref,
        "agents": config.AGENT_CHOICES,
        "app_name": "LIFI",
        "social_links": config.SOCIAL_LINKS,
        "app_store_url": config.APP_STORE_URL,
        "play_store_url": config.PLAY_STORE_URL,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("quoter.quoter_page"))


@app.route("/dashboard")
def legacy_dashboard():
    return redirect(url_for("quoter.quoter_page"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=True)
