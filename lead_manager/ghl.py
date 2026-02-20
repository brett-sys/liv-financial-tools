"""Go High Level API helpers — upsert contacts from CSV leads with agent tags."""

import requests
import config

GHL_BASE_URL = "https://services.leadconnectorhq.com"


def _headers():
    return {
        "Authorization": f"Bearer {config.GHL_API_KEY}",
        "Version": "2021-07-28",
    }


def check_config():
    """Return an error string if GHL isn't configured, else None."""
    if not config.GHL_API_KEY:
        return "GHL_API_KEY not set in .env"
    if not config.GHL_LOCATION_ID:
        return "GHL_LOCATION_ID not set in .env"
    return None


def import_lead(lead, agent_name, extra_tags=None):
    """Push a CSV lead into GHL as a contact, tagged with agent name.

    Returns dict with success, contact_id, message.
    """
    err = check_config()
    if err:
        return {"success": False, "contact_id": None, "message": err}

    tags = [agent_name]
    if extra_tags:
        tags.extend(extra_tags)

    payload = {
        "locationId": config.GHL_LOCATION_ID,
        "firstName": lead.get("first_name", ""),
        "lastName": lead.get("last_name", ""),
        "name": lead.get("full_name", ""),
        "tags": tags,
    }

    if lead.get("email"):
        payload["email"] = lead["email"]
    if lead.get("phone"):
        payload["phone"] = lead["phone"]
    if lead.get("address"):
        payload["address1"] = lead["address"]
    if lead.get("city"):
        payload["city"] = lead["city"]
    if lead.get("state"):
        payload["state"] = lead["state"]
    if lead.get("zip"):
        payload["postalCode"] = lead["zip"]
    if lead.get("dob"):
        payload["dateOfBirth"] = lead["dob"]

    # Pack extra info into customFields or source
    payload["source"] = lead.get("vendor", "CSV Import")

    try:
        resp = requests.post(
            f"{GHL_BASE_URL}/contacts/upsert",
            json=payload,
            headers={**_headers(), "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.ConnectionError:
        return {"success": False, "contact_id": None, "message": "Could not connect to GHL"}
    except requests.Timeout:
        return {"success": False, "contact_id": None, "message": "GHL request timed out"}

    if resp.status_code == 200:
        data = resp.json()
        contact = data.get("contact", {})
        contact_id = contact.get("id")
        if contact_id:
            name = lead.get("full_name", "Unknown")
            return {
                "success": True,
                "contact_id": contact_id,
                "message": f"{name} → tagged '{agent_name}'",
            }
        return {"success": False, "contact_id": None, "message": f"GHL OK but no ID: {data}"}

    if resp.status_code == 401:
        return {"success": False, "contact_id": None, "message": "GHL auth failed — check API key"}
    if resp.status_code == 422:
        return {"success": False, "contact_id": None, "message": f"GHL rejected: {resp.text}"}

    return {"success": False, "contact_id": None, "message": f"GHL error ({resp.status_code})"}
