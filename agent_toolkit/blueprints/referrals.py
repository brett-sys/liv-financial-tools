"""Referrals blueprint – add, list, update status, stats."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from models.referrals import (
    add_referral, get_all_referrals, update_status,
    delete_referral, get_stats, STATUSES,
)

referrals_bp = Blueprint("referrals", __name__)


@referrals_bp.route("/")
def referrals_page():
    referrals = get_all_referrals()
    stats = get_stats()
    return render_template(
        "referrals.html",
        referrals=referrals,
        stats=stats,
        statuses=STATUSES,
    )


@referrals_bp.route("/add", methods=["POST"])
def add():
    referrer = request.form.get("referrer_name", "").strip()
    referred = request.form.get("referred_name", "").strip()
    if not referrer or not referred:
        flash("Referrer and Referred Person are required.", "error")
        return redirect(url_for("referrals.referrals_page"))

    add_referral(
        referrer_name=referrer,
        referred_name=referred,
        phone=request.form.get("referred_phone", "").strip(),
        email=request.form.get("referred_email", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    flash("Referral added!", "success")
    return redirect(url_for("referrals.referrals_page"))


@referrals_bp.route("/update/<int:row_id>", methods=["POST"])
def update(row_id):
    new_status = request.form.get("status", "")
    premium = request.form.get("premium", "").strip()
    if new_status:
        update_status(row_id, new_status, premium)
        flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("referrals.referrals_page"))


@referrals_bp.route("/delete/<int:row_id>", methods=["POST"])
def delete(row_id):
    delete_referral(row_id)
    flash("Referral deleted.", "success")
    return redirect(url_for("referrals.referrals_page"))
