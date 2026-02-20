"""PDF generation (WeasyPrint + API) and browser launcher."""

import subprocess
import tempfile
from pathlib import Path

import requests
from weasyprint import HTML as WeasyHTML

from .config import API_KEY, API_ENDPOINT_TEMPLATE


class PDFGenerationError(Exception):
    """Raised when PDF generation fails, with a user-friendly message."""
    pass


class APIError(Exception):
    """Raised when the remote API is unreachable or returns an error."""
    pass


def generate_pdf(html_content: str) -> str:
    """Generate PDF locally using WeasyPrint. Returns file:// URL to the PDF."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        WeasyHTML(string=html_content).write_pdf(pdf_path)
        return Path(pdf_path).resolve().as_uri()
    except Exception as e:
        raise PDFGenerationError(
            f"WeasyPrint PDF generation failed: {e}\n\n"
            "Make sure WeasyPrint and its system dependencies are installed.\n"
            "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
        ) from e


def generate_pdf_from_template(template_id: str, data: dict) -> str:
    """Generate PDF from an API Template (e.g. business card). Returns download_url."""
    if not API_KEY:
        raise APIError(
            "API key not configured.\n\n"
            "Set APITEMPLATE_API_KEY in your .env file to use template-based PDF generation."
        )
    payload = {
        "template_id": template_id,
        "data": data,
    }
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            API_ENDPOINT_TEMPLATE, json=payload, headers=headers, timeout=30
        )
    except requests.ConnectionError:
        raise APIError(
            "Could not connect to APITemplate.io.\n\n"
            "Check your internet connection and try again."
        )
    except requests.Timeout:
        raise APIError(
            "Request to APITemplate.io timed out after 30 seconds.\n\n"
            "The service may be temporarily unavailable. Try again later."
        )

    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        raise APIError(result.get("message", "Unknown API error"))
    raise APIError(f"HTTP {response.status_code}: {response.text}")


def open_chrome(url: str) -> bool:
    """Open URL in Chrome. Returns True if Chrome was launched, False if fallback used."""
    try:
        subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', url])
        return True
    except Exception:
        try:
            subprocess.Popen(['open', '-a', 'Google Chrome', url])
            return True
        except Exception:
            try:
                subprocess.Popen(['open', url])
            except Exception:
                # All methods failed — caller should show the URL to the user
                return False
            return False
