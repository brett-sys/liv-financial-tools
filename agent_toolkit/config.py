"""LIFI Agent Toolkit – unified configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Database paths
# ---------------------------------------------------------------------------
CALLS_DB_PATH = BASE_DIR / "calls.db"
REFERRALS_DB_PATH = BASE_DIR / "referrals.db"

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("CALL_LOGGER_SECRET_KEY", "lifi-dev-key-change-me")
HOST = os.getenv("LIFI_HOST", "0.0.0.0")
PORT = int(os.getenv("LIFI_PORT", os.getenv("CALL_LOGGER_PORT", "5055")))

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------
GOOGLE_SHEETS_CREDENTIALS = BASE_DIR / "credentials.json"
CALL_LOG_SHEET_ID = os.getenv("CALL_LOG_SHEET_ID", "")

# ---------------------------------------------------------------------------
# Scheduler (weekly Google Sheets export)
# ---------------------------------------------------------------------------
REPORT_DAY = "fri"
REPORT_HOUR = 18
REPORT_MINUTE = 0

# ---------------------------------------------------------------------------
# Agents (expandable – add new agents here)
# ---------------------------------------------------------------------------
AGENTS = [
    {
        "name": "Brett",
        "email": "brett@fflliv.com",
        "theme": "brett",
        "calendar": "google",
    },
    {
        "name": "Kevin Nelson",
        "email": "kevinnelsonk2@outlook.com",
        "theme": "kevin",
        "calendar": "outlook",
    },
    {
        "name": "Easton",
        "email": "",
        "theme": "easton",
        "calendar": "google",
    },
    {
        "name": "Joe",
        "email": "",
        "theme": "joe",
        "calendar": "google",
    },
]

AGENT_CHOICES = [a["name"] for a in AGENTS]
AGENT_EMAILS = {a["name"]: a["email"] for a in AGENTS}
AGENT_THEMES = {a["name"]: a["theme"] for a in AGENTS}
AGENT_CALENDAR_TYPES = {a["name"]: a["calendar"] for a in AGENTS}

# ---------------------------------------------------------------------------
# Call field options
# ---------------------------------------------------------------------------
DIRECTION_CHOICES = ["Inbound", "Outbound"]
OUTCOME_CHOICES = ["Sale", "Callback", "No Answer", "Voicemail", "Not Interested", "Other"]

CALENDAR_REMINDER_MINUTES = 30

# ---------------------------------------------------------------------------
# Go High Level CRM
# ---------------------------------------------------------------------------
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_WORKFLOW_ID = os.getenv("GHL_WORKFLOW_ID", "")
GHL_FILE_CUSTOM_FIELD_ID = os.getenv("GHL_FILE_CUSTOM_FIELD_ID", "")
GHL_ENABLED = os.getenv("GHL_ENABLED", "false").lower() in ("true", "1", "yes")
GHL_BASE_URL = "https://services.leadconnectorhq.com"

# ---------------------------------------------------------------------------
# PDF Engine
# ---------------------------------------------------------------------------
PDF_ENGINE_DIR = BASE_DIR / "pdf_engine"
LOGO_FILENAME = "assets/234.png"
NLG_LOGO_FILENAME = "assets/nlg_logo.png"
AGENT_PHOTO_FILENAME = "assets/agent_headshot.png"
BUSINESS_CARD_FILENAME = "assets/business_card.png"

AGENT_NAME = "Brett Dunham"
AGENT_TITLE = "Agency Owner"
AGENT_PHONE = "(714) 335-1412"
AGENT_EMAIL_DISPLAY = "brett@fflliv.com"
AGENT_LICENSE = "License #21114292"
AGENT_WEBSITE = "www.livfinancialgroup.com"

# ---------------------------------------------------------------------------
# Integrity Connect (Quoter)
# ---------------------------------------------------------------------------
INTEGRITY_URL = "https://connect.integrity.com"

# ---------------------------------------------------------------------------
# Web Push (VAPID)
# ---------------------------------------------------------------------------
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "brett@fflliv.com")
