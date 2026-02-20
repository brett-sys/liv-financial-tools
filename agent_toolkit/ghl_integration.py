"""Go High Level CRM integration – upsert contacts, upload PDFs, trigger workflows."""

from pathlib import Path
import requests

import config


class GHLError(Exception):
    pass


def _headers():
    return {
        "Authorization": f"Bearer {config.GHL_API_KEY}",
        "Version": "2021-07-28",
    }


def _check_config():
    if not config.GHL_ENABLED:
        return "GHL integration is disabled (set GHL_ENABLED=true in .env)"
    if not config.GHL_API_KEY or config.GHL_API_KEY == "your_ghl_api_key_here":
        return "GHL API key not configured (set GHL_API_KEY in .env)"
    if not config.GHL_LOCATION_ID or config.GHL_LOCATION_ID == "your_location_id_here":
        return "GHL Location ID not configured (set GHL_LOCATION_ID in .env)"
    return None


def upsert_contact(name, email=None, phone=None):
    err = _check_config()
    if err:
        raise GHLError(err)

    parts = name.strip().split(None, 1)
    first_name = parts[0] if parts else name.strip()
    last_name = parts[1] if len(parts) > 1 else ""

    payload = {
        "locationId": config.GHL_LOCATION_ID,
        "firstName": first_name,
        "lastName": last_name,
        "name": name.strip(),
    }
    if email:
        payload["email"] = email.strip()
    if phone:
        payload["phone"] = phone.strip()

    try:
        resp = requests.post(
            f"{config.GHL_BASE_URL}/contacts/upsert",
            json=payload,
            headers={**_headers(), "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.ConnectionError:
        raise GHLError("Could not connect to Go High Level.")
    except requests.Timeout:
        raise GHLError("Go High Level request timed out.")

    if resp.status_code == 200:
        data = resp.json()
        contact = data.get("contact", {})
        contact_id = contact.get("id")
        if contact_id:
            return contact_id
        raise GHLError(f"GHL returned success but no contact ID: {data}")

    if resp.status_code == 401:
        raise GHLError("GHL authentication failed. Check your GHL_API_KEY in .env")
    if resp.status_code == 422:
        raise GHLError(f"GHL rejected the contact data: {resp.text}")

    raise GHLError(f"GHL upsert failed (HTTP {resp.status_code}): {resp.text}")


def upload_pdf_to_contact(contact_id, pdf_path, filename="illustration.pdf"):
    if not config.GHL_FILE_CUSTOM_FIELD_ID or config.GHL_FILE_CUSTOM_FIELD_ID == "your_custom_field_id_here":
        raise GHLError("GHL file custom field ID not configured.")

    path = Path(pdf_path)
    if not path.exists():
        raise GHLError(f"PDF file not found: {pdf_path}")

    try:
        with open(path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            data = {
                "contactId": contact_id,
                "locationId": config.GHL_LOCATION_ID,
            }
            resp = requests.post(
                f"{config.GHL_BASE_URL}/forms/upload-custom-files",
                files=files, data=data, headers=_headers(), timeout=30,
            )
    except requests.ConnectionError:
        raise GHLError("Could not connect to GHL for file upload.")
    except requests.Timeout:
        raise GHLError("GHL file upload timed out.")

    if resp.status_code in (200, 201):
        return True
    if resp.status_code == 401:
        raise GHLError("GHL authentication failed during file upload.")
    raise GHLError(f"GHL file upload failed (HTTP {resp.status_code}): {resp.text}")


def send_to_ghl(client_name, pdf_path, email=None, phone=None):
    result = {"success": False, "message": "", "steps": {"contact": False, "upload": False}}

    err = _check_config()
    if err:
        result["message"] = err
        return result

    if not client_name or not client_name.strip():
        result["message"] = "No client name provided."
        return result

    status_parts = []
    try:
        contact_id = upsert_contact(client_name, email=email, phone=phone)
        result["steps"]["contact"] = True
        status_parts.append("Contact synced")
    except GHLError as e:
        result["message"] = f"Contact sync failed: {e}"
        return result

    filename = f"{client_name.strip().replace(' ', '_')}_illustration.pdf"
    try:
        upload_pdf_to_contact(contact_id, pdf_path, filename=filename)
        result["steps"]["upload"] = True
        status_parts.append("PDF uploaded")
    except GHLError as e:
        status_parts.append(f"PDF upload failed: {e}")

    result["success"] = result["steps"]["contact"]
    result["message"] = " | ".join(status_parts)
    return result
