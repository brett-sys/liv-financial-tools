"""Configuration for Call Logger app."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# Database
DATABASE_PATH = BASE_DIR / "calls.db"

# Google Sheets credentials
# On Railway: reads from GOOGLE_CREDENTIALS_JSON env variable
# Locally: reads from credentials.json file
_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if _creds_json:
    GOOGLE_SHEETS_CREDENTIALS = Path("/tmp/gcp_credentials.json")
    GOOGLE_SHEETS_CREDENTIALS.write_text(_creds_json)
else:
    GOOGLE_SHEETS_CREDENTIALS = BASE_DIR / "credentials.json"
CALL_LOG_SHEET_ID = os.getenv("CALL_LOG_SHEET_ID", "")

# Flask
SECRET_KEY = os.getenv("CALL_LOGGER_SECRET_KEY", "call-logger-dev-key-change-me")
HOST = os.getenv("CALL_LOGGER_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("CALL_LOGGER_PORT", "5055")))

# Scheduler
REPORT_DAY = "fri"
REPORT_HOUR = 18
REPORT_MINUTE = 0

# Call field options
DIRECTION_CHOICES = ["Inbound", "Outbound"]
OUTCOME_CHOICES = ["Sale", "Callback", "No Answer", "Voicemail", "Not Interested", "Other"]
AGENT_CHOICES = ["Brett", "Kevin Nelson", "Easton Passolt", "Joe"]

# Agent email mapping for calendar invites
AGENT_EMAILS = {
    "Brett": "brett@fflliv.com",
    "Kevin Nelson": "kevinnelsonk2@outlook.com",
    "Easton Passolt": "eastonpassolt.ffl@gmail.com",
    "Joe": "everyoneneedsajoe@gmail.com",
}

# Calendar reminder (minutes before event)
CALENDAR_REMINDER_MINUTES = 30
