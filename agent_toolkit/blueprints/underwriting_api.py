"""Underwriting API blueprint – JSON endpoint for carrier risk assessment."""

import sys
from pathlib import Path

from flask import Blueprint, request, jsonify

# The underwriting module lives at ../underwriting/ relative to agent_toolkit/
_UW_DIR = Path(__file__).resolve().parent.parent.parent / "underwriting"
if str(_UW_DIR) not in sys.path:
    sys.path.insert(0, str(_UW_DIR))

underwriting_bp = Blueprint("underwriting", __name__)


def _get_uw():
    """Lazy import to avoid startup errors if DB not yet initialized."""
    import underwriting_tool as uw
    uw.init_db()
    return uw


@underwriting_bp.route("/assess", methods=["POST"])
def assess():
    """Assess a client against all carriers for a product type.

    Expects JSON body:
        age              (int, required)
        height_inches    (float, optional) – height in inches
        weight_lbs       (float, optional) – weight in pounds
        tobacco          (bool, default false)
        diabetes         (bool, default false)
        hypertension     (bool, default false)
        cancer_years_ago (int, optional)   – years since cancer, omit if none
        dui_years_ago    (int, optional)   – years since DUI, omit if none
        conditions       (list[str], optional) – condition codes (e.g. ["copd", "stroke_tia"])
        product_type     (str, default "IUL") – "IUL", "Term", or "Final Expense"

    Returns JSON:
        results: list of {carrier, rating, notes, declined}
        client:  echo of parsed client profile (with computed BMI)
    """
    payload = request.get_json(silent=True) or {}

    age = payload.get("age")
    if age is None:
        return jsonify({"success": False, "error": "age is required"}), 400
    try:
        age = int(age)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "age must be a number"}), 400

    height = payload.get("height_inches")
    weight = payload.get("weight_lbs")
    try:
        height = float(height) if height is not None else None
        weight = float(weight) if weight is not None else None
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "height_inches and weight_lbs must be numbers"}), 400

    bmi = None
    if height and weight and height > 0:
        bmi = round(weight / (height * height) * 703, 1)

    cancer = payload.get("cancer_years_ago")
    if cancer is not None:
        try:
            cancer = int(cancer)
        except (ValueError, TypeError):
            cancer = 999
    else:
        cancer = 999

    dui = payload.get("dui_years_ago")
    if dui is not None:
        try:
            dui = int(dui)
        except (ValueError, TypeError):
            dui = 999
    else:
        dui = 999

    conditions = set(payload.get("conditions") or [])
    product_type = payload.get("product_type", "IUL")
    if product_type not in ("IUL", "Term", "Final Expense"):
        return jsonify({"success": False, "error": "product_type must be IUL, Term, or Final Expense"}), 400

    client = {
        "age": age,
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "tobacco": bool(payload.get("tobacco", False)),
        "diabetes": bool(payload.get("diabetes", False)),
        "hypertension": bool(payload.get("hypertension", False)),
        "cancer_history_years": cancer,
        "dui_years_ago": dui,
        "conditions": conditions,
    }

    try:
        uw = _get_uw()
        carriers = uw.get_carriers(product_type=product_type)
        if not carriers:
            return jsonify({
                "success": True,
                "results": [],
                "message": f"No {product_type} carriers in database.",
                "client": _serialize_client(client),
            })

        results = uw.assess(client, carriers)
    except Exception as e:
        return jsonify({"success": False, "error": f"Assessment failed: {e}"}), 500

    return jsonify({
        "success": True,
        "results": results,
        "client": _serialize_client(client),
    })


@underwriting_bp.route("/conditions", methods=["GET"])
def list_conditions():
    """Return all available condition codes for use in /assess requests."""
    try:
        uw = _get_uw()
        conditions = uw.get_conditions()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "conditions": conditions})


@underwriting_bp.route("/carriers", methods=["GET"])
def list_carriers():
    """Return all carriers, optionally filtered by product_type query param."""
    product_type = request.args.get("product_type")
    try:
        uw = _get_uw()
        carriers = uw.get_carriers(product_type=product_type)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "carriers": carriers})


def _serialize_client(client: dict) -> dict:
    """Make the client dict JSON-safe (sets → lists)."""
    c = dict(client)
    if "conditions" in c and isinstance(c["conditions"], set):
        c["conditions"] = sorted(c["conditions"])
    return c
