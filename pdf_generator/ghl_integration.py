"""Go High Level (GHL) CRM integration — upsert contacts, upload PDFs, trigger workflows."""

from pathlib import Path

import requests

from .config import (
    GHL_API_KEY,
    GHL_BASE_URL,
    GHL_ENABLED,
    GHL_FILE_CUSTOM_FIELD_ID,
    GHL_LOCATION_ID,
    GHL_WORKFLOW_ID,
)


class GHLError(Exception):
    """Raised when a GHL API call fails, with a user-friendly message."""
    pass


def _headers() -> dict:
    """Standard auth + version headers for GHL API v2."""
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Version": "2021-07-28",
    }


def _check_config() -> str | None:
    """Return an error message if GHL is not properly configured, else None."""
    if not GHL_ENABLED:
        return "GHL integration is disabled (set GHL_ENABLED=true in .env)"
    if not GHL_API_KEY or GHL_API_KEY == "your_ghl_api_key_here":
        return "GHL API key not configured (set GHL_API_KEY in .env)"
    if not GHL_LOCATION_ID or GHL_LOCATION_ID == "your_location_id_here":
        return "GHL Location ID not configured (set GHL_LOCATION_ID in .env)"
    return None


def upsert_contact(
    name: str,
    email: str | None = None,
    phone: str | None = None,
) -> str:
    """Create or update a contact in GHL. Returns the contact ID.

    At least a name is required. Email or phone improves deduplication.
    """
    parts = name.strip().split(None, 1)
    first_name = parts[0] if parts else name.strip()
    last_name = parts[1] if len(parts) > 1 else ""

    payload: dict = {
        "locationId": GHL_LOCATION_ID,
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
            f"{GHL_BASE_URL}/contacts/upsert",
            json=payload,
            headers={**_headers(), "Content-Type": "application/json"},
            timeout=15,
        )
    except requests.ConnectionError:
        raise GHLError("Could not connect to Go High Level. Check your internet connection.")
    except requests.Timeout:
        raise GHLError("Go High Level request timed out. Try again later.")

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

    raise GHLError(f"GHL upsert contact failed (HTTP {resp.status_code}): {resp.text}")


def upload_pdf_to_contact(contact_id: str, pdf_path: str, filename: str = "illustration.pdf") -> bool:
    """Upload a PDF file to a contact's file custom field in GHL.

    Returns True on success.
    """
    if not GHL_FILE_CUSTOM_FIELD_ID or GHL_FILE_CUSTOM_FIELD_ID == "your_custom_field_id_here":
        raise GHLError(
            "GHL file custom field ID not configured.\n"
            "Create a File Upload custom field in GHL (Settings > Custom Fields),\n"
            "then set GHL_FILE_CUSTOM_FIELD_ID in your .env file."
        )

    path = Path(pdf_path)
    if not path.exists():
        raise GHLError(f"PDF file not found: {pdf_path}")

    # GHL file upload uses multipart form data
    # The field key format is: {custom_field_id}
    try:
        with open(path, "rb") as f:
            files = {
                "file": (filename, f, "application/pdf"),
            }
            data = {
                "contactId": contact_id,
                "locationId": GHL_LOCATION_ID,
            }
            # Use the custom field file upload endpoint
            resp = requests.post(
                f"{GHL_BASE_URL}/forms/upload-custom-files",
                files=files,
                data=data,
                headers=_headers(),
                timeout=30,
            )
    except requests.ConnectionError:
        raise GHLError("Could not connect to GHL for file upload.")
    except requests.Timeout:
        raise GHLError("GHL file upload timed out.")

    if resp.status_code in (200, 201):
        return True

    # Fallback: try updating the contact's custom field with a note about the PDF
    if resp.status_code == 401:
        raise GHLError("GHL authentication failed during file upload. Check your GHL_API_KEY.")

    raise GHLError(f"GHL file upload failed (HTTP {resp.status_code}): {resp.text}")


def trigger_workflow(contact_id: str) -> bool:
    """Add a contact to the configured GHL workflow. Returns True on success."""
    if not GHL_WORKFLOW_ID or GHL_WORKFLOW_ID == "your_workflow_id_here":
        return False  # Silently skip if no workflow configured

    try:
        resp = requests.post(
            f"{GHL_BASE_URL}/contacts/{contact_id}/workflow/{GHL_WORKFLOW_ID}",
            headers={**_headers(), "Content-Type": "application/json"},
            json={},
            timeout=15,
        )
    except requests.ConnectionError:
        raise GHLError("Could not connect to GHL to trigger workflow.")
    except requests.Timeout:
        raise GHLError("GHL workflow trigger timed out.")

    if resp.status_code == 200:
        return True

    if resp.status_code == 401:
        raise GHLError("GHL authentication failed for workflow trigger. Check your GHL_API_KEY.")
    if resp.status_code == 422:
        raise GHLError(f"GHL rejected the workflow trigger: {resp.text}")

    raise GHLError(f"GHL workflow trigger failed (HTTP {resp.status_code}): {resp.text}")


def send_to_ghl(
    client_name: str,
    pdf_path: str,
    email: str | None = None,
    phone: str | None = None,
) -> dict:
    """Orchestrate the full GHL sync: upsert contact, upload PDF, trigger workflow.

    Returns a dict with:
        - success: bool — True if all steps succeeded
        - message: str  — human-readable summary
        - steps: dict   — status of each step (contact, upload, workflow)
    """
    result = {
        "success": False,
        "message": "",
        "steps": {"contact": False, "upload": False, "workflow": False},
    }

    # Pre-flight config check
    config_err = _check_config()
    if config_err:
        result["message"] = config_err
        return result

    if not client_name or not client_name.strip():
        result["message"] = "No client name provided for GHL sync."
        return result

    status_parts = []

    # Step 1: Upsert contact
    try:
        contact_id = upsert_contact(client_name, email=email, phone=phone)
        result["steps"]["contact"] = True
        status_parts.append("Contact synced")
    except GHLError as e:
        result["message"] = f"GHL contact sync failed: {e}"
        return result

    # Step 2: Upload PDF
    filename = f"{client_name.strip().replace(' ', '_')}_illustration.pdf"
    try:
        upload_pdf_to_contact(contact_id, pdf_path, filename=filename)
        result["steps"]["upload"] = True
        status_parts.append("PDF uploaded")
    except GHLError as e:
        status_parts.append(f"PDF upload failed: {e}")

    # Step 3: Trigger workflow
    try:
        triggered = trigger_workflow(contact_id)
        if triggered:
            result["steps"]["workflow"] = True
            status_parts.append("Workflow triggered")
        else:
            status_parts.append("No workflow configured")
    except GHLError as e:
        status_parts.append(f"Workflow failed: {e}")

    result["success"] = result["steps"]["contact"]
    result["message"] = " | ".join(status_parts)
    return result
