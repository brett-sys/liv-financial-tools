"""Configuration for Lead Manager app."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# Google service account credentials
# On Railway: reads from GOOGLE_CREDENTIALS_JSON env variable
# Locally: reads from call_logger/credentials.json file
_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if _creds_json:
    GOOGLE_CREDENTIALS = Path("/tmp/gcp_credentials.json")
    GOOGLE_CREDENTIALS.write_text(_creds_json)
else:
    GOOGLE_CREDENTIALS = PROJECT_ROOT / "call_logger" / "credentials.json"

# Google Drive folder containing lead CSVs
DRIVE_FOLDER_ID = os.getenv("LEAD_DRIVE_FOLDER_ID", "1qfo-He84pnSfA5qhtowJ_1FKL0rWdRqL")

# Flask
SECRET_KEY = os.getenv("LEAD_MANAGER_SECRET_KEY", "lead-mgr-dev-key-change-me")
HOST = os.getenv("LEAD_MANAGER_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT") or os.getenv("LEAD_MANAGER_PORT", "5070"))

# Go High Level (Elite 360)
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")

# Agents config file
AGENTS_FILE = BASE_DIR / "agents.json"

# CSV column mapping — maps our internal keys to CSV header names
CSV_COLUMNS = {
    "full_name": "Full Name",
    "first_name": "First Name",
    "last_name": "Last Name",
    "dob": "Date Of Birth",
    "age": "Age",
    "email": "Email",
    "phone": "Phone Number",
    "address": "Street Address",
    "city": "City",
    "state": "State",
    "zip": "Zip Code",
    "created": "Created Date",
    "insured": "Currently Insured",
    "military": "Is Military",
    "marital": "Marital Status",
    "dui": "DUI",
    "tobacco": "Tobacco",
    "medical_type": "Major Medical Type",
    "height": "Height Inches",
    "weight": "Weight Lbs",
    "prescriptions": "Prescription Medications",
    "coverage_type": "Coverage Type Option",
    "coverage_amount": "Requested Coverage Amount",
    "hazards": "Hazards",
    "vendor": "Vendor",
}


def load_agents():
    """Load agents from JSON config file."""
    if AGENTS_FILE.exists():
        with open(AGENTS_FILE) as f:
            return json.load(f)
    return []


def save_agents(agents):
    """Save agents to JSON config file."""
    with open(AGENTS_FILE, "w") as f:
        json.dump(agents, f, indent=2)
