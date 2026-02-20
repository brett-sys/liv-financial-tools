"""Google Drive helpers — list CSV files and parse lead data."""

import csv
import io
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import config

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_service():
    creds_path = config.GOOGLE_CREDENTIALS
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found at {creds_path}")
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def list_csv_files():
    """List all CSV files in the configured Drive folder.

    Returns list of dicts with id, name, state, date, size.
    """
    service = _get_service()
    folder_id = config.DRIVE_FOLDER_ID

    all_files = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='text/csv'",
            pageSize=100,
            fields="nextPageToken, files(id, name, size, modifiedTime)",
            orderBy="name",
            pageToken=page_token,
        ).execute()
        all_files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    results = []
    for f in all_files:
        state = _parse_state(f["name"])
        results.append({
            "id": f["id"],
            "name": f["name"],
            "state": state or "??",
            "size": _human_size(int(f.get("size", 0))),
            "modified": f.get("modifiedTime", "")[:10],
        })
    return results


def download_csv(file_id):
    """Download a CSV file from Drive and return parsed rows as list of dicts."""
    service = _get_service()
    content = service.files().get_media(fileId=file_id).execute()
    text = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    leads = []
    col_map = config.CSV_COLUMNS

    for i, row in enumerate(reader):
        lead = {"_index": i}
        for key, csv_header in col_map.items():
            lead[key] = row.get(csv_header, "").strip()
        leads.append(lead)

    return leads


def _parse_state(filename):
    """Extract state abbreviation from filename like leads_FL_2026-02-01.csv."""
    m = re.match(r"leads_([A-Z]{2})_", filename)
    return m.group(1) if m else None


def _human_size(nbytes):
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}" if unit == "B" else f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"
