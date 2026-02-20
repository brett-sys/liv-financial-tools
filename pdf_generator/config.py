"""Configuration constants, environment loading, and agent info."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level up from this script's folder)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Paths
PACKAGE_DIR = Path(__file__).resolve().parent

# API Configuration (used by Business Card template only)
API_KEY = os.environ.get("APITEMPLATE_API_KEY", "")
API_ENDPOINT_TEMPLATE = "https://rest.apitemplate.io/v2/create-pdf"
POLICY_SUBMITTED_TEMPLATE_ID = "58777b23c9701b0e"
BUSINESS_CARD_TEMPLATE_ID = "f9177b23cf19f372"
LOGO_FILENAME = "assets/234.png"
NLG_LOGO_FILENAME = "assets/nlg_logo.png"

# Agent info (shown in PDF header) — update these with your real details
AGENT_NAME = "Brett Dunham"
AGENT_TITLE = "Agency Owner"
AGENT_PHONE = "(714) 335-1412"
AGENT_EMAIL = "brett@fflliv.com"
AGENT_LICENSE = "License #21114292"
AGENT_WEBSITE = "www.livfinancialgroup.com"
AGENT_PHOTO_FILENAME = "assets/agent_headshot.png"
BUSINESS_CARD_FILENAME = "assets/business_card.png"

# Go High Level (GHL) CRM Integration
GHL_API_KEY = os.environ.get("GHL_API_KEY", "")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "")
GHL_WORKFLOW_ID = os.environ.get("GHL_WORKFLOW_ID", "")
GHL_FILE_CUSTOM_FIELD_ID = os.environ.get("GHL_FILE_CUSTOM_FIELD_ID", "")
GHL_ENABLED = os.environ.get("GHL_ENABLED", "false").lower() in ("true", "1", "yes")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
