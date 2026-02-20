"""Google Sheets export for Call Logger.

Uses a Google Cloud service account + gspread to push weekly call data
to a Google Sheet. Each week gets its own tab named by date range.
"""

from datetime import datetime, timedelta

import config

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER_ROW = [
    "Agent", "Date/Time", "Contact Name", "Phone Number",
    "Direction", "Outcome", "Notes", "Follow-up Date",
]


def _get_client():
    """Authenticate and return a gspread client."""
    if not SHEETS_AVAILABLE:
        raise RuntimeError(
            "gspread / google-auth not installed. "
            "Run: pip install gspread google-auth"
        )
    creds_path = config.GOOGLE_SHEETS_CREDENTIALS
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Google credentials not found at {creds_path}. "
            "See README for setup instructions."
        )
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def _week_label():
    """Return a human-readable label for the current Mon-Fri week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return f"{monday.strftime('%b %d')}-{friday.strftime('%d, %Y')}"


def _export_agent_tab(spreadsheet, agent_name, calls, week_label):
    """Write one agent's calls to their own tab and return the tab name."""
    tab_name = f"{agent_name} - {week_label}"

    try:
        worksheet = spreadsheet.worksheet(tab_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=200, cols=10)

    agent_calls = [c for c in calls if c["agent_name"] == agent_name]

    rows = [HEADER_ROW]
    outcome_totals = {}
    for c in agent_calls:
        rows.append([
            c["agent_name"],
            c["call_datetime"],
            c["contact_name"],
            c["phone_number"],
            c["direction"],
            c["outcome"],
            c["notes"],
            c["follow_up_date"] or "",
        ])
        outcome_totals[c["outcome"]] = outcome_totals.get(c["outcome"], 0) + 1

    rows.append([])
    rows.append(["SUMMARY"])
    rows.append(["Total Calls", str(len(agent_calls))])
    for outcome, count in sorted(outcome_totals.items(), key=lambda x: -x[1]):
        rows.append([f"  {outcome}", str(count)])

    worksheet.update(rows, value_input_option="RAW")
    worksheet.format("1:1", {"textFormat": {"bold": True}})

    return tab_name


def export_week_to_sheets():
    """Export the current week's calls to per-agent tabs in Google Sheets.

    Creates one tab per agent (e.g. "Brett - Feb 17-21, 2026").
    Returns a comma-separated string of created tab names.
    """
    import models

    sheet_id = config.CALL_LOG_SHEET_ID
    if not sheet_id:
        raise ValueError(
            "CALL_LOG_SHEET_ID not set in .env. "
            "Create a Google Sheet, copy the sheet ID from its URL, and add it to .env."
        )

    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    week = _week_label()
    calls = models.get_week_calls()

    created_tabs = []
    for agent in config.AGENT_CHOICES:
        tab = _export_agent_tab(spreadsheet, agent, calls, week)
        created_tabs.append(tab)

    return ", ".join(created_tabs)
