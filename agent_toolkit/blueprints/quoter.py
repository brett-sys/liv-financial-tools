"""Quoter blueprint – Integrity Connect iframe embed."""

from flask import Blueprint, render_template
import config

quoter_bp = Blueprint("quoter", __name__)


@quoter_bp.route("/")
def quoter_page():
    return render_template("quoter.html", integrity_url=config.INTEGRITY_URL)
