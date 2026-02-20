"""LIFI Agent Toolkit – main Flask application."""

from flask import Flask, request, make_response, redirect, url_for

import config
from models.calls import init_db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with app.app_context():
    init_db()

# ---------------------------------------------------------------------------
# Register blueprints
# ---------------------------------------------------------------------------
from blueprints.calls import calls_bp       # noqa: E402
from blueprints.quoter import quoter_bp     # noqa: E402
from blueprints.tools import tools_bp       # noqa: E402
from blueprints.referrals import referrals_bp  # noqa: E402

app.register_blueprint(calls_bp)
app.register_blueprint(quoter_bp, url_prefix="/quoter")
app.register_blueprint(tools_bp, url_prefix="/tools")
app.register_blueprint(referrals_bp, url_prefix="/referrals")


# ---------------------------------------------------------------------------
# Theme: set via /<agent_slug>, detected by hostname, stored in cookie
# ---------------------------------------------------------------------------
THEME_ROUTES = {}
for agent in config.AGENTS:
    slug = agent["name"].lower().replace(" ", "")
    THEME_ROUTES[slug] = agent


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
        host = request.host.split(":")[0]
        is_local = host in ("localhost", "127.0.0.1") or host.startswith("192.168.")
        theme = "brett" if is_local else "kevin"
        agent_pref = "Brett" if is_local else "Kevin Nelson"
    return {
        "theme": theme,
        "agent_pref": agent_pref,
        "agents": config.AGENT_CHOICES,
        "app_name": "LIFI",
        "vapid_public_key": config.VAPID_PUBLIC_KEY,
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
