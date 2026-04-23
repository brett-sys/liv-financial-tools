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

# Agent registry: URL slug -> display name
AGENT_ROUTES = {
    "brett": "Brett",
    "kevin": "Kevin Nelson",
    "easton": "Easton Passolt",
    "joe": "Joe",
    "kooper": "Kooper",
    "kaiden": "Kaiden",
    "alex": "Alex",
    "pedro": "Pedro",
    "quavo": "Quavo",
    "mahan": "Mahan",
    "deven": "Deven",
    "carmello": "Carmello",
    "daniel": "Daniel",
    "manuel": "Manuel",
    "nico": "Nico",
    "jean": "Jean",
}

AGENT_CHOICES = list(AGENT_ROUTES.values())

# Agent email mapping for calendar invites
AGENT_EMAILS = {
    "Brett": "brett@fflliv.com",
    "Kevin Nelson": "kevinnelsonk2@outlook.com",
    "Easton Passolt": "eastonpassolt.ffl@gmail.com",
    "Joe": "everyoneneedsajoe@gmail.com",
    "Kaiden": "Kaidenkranz1@gmail.com",
    "Alex": "alexvalle.liv.financial@gmail.com",
    "Pedro": "prtrading13@gmail.com",
    "Quavo": "Cordaekennedy28@gmail.com",
    "Mahan": "Mahan@empirefia.com",
    "Deven": "devenworldsffl@gmail.com",
    "Carmello": "carmello@elevatedfia.com",
    "Daniel": "danielvareaghin1@gmail.com",
    "Manuel": "msvargas2407@gmail.com",
    "Nico": "Nicovilgil08@gmail.com",
    "Jean": "jeancoral07@gmail.com",
}

# Calendar reminder (minutes before event)
CALENDAR_REMINDER_MINUTES = 30
