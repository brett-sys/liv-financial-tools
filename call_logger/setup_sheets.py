"""
Google Sheets Setup Wizard for Call Logger
==========================================
Run this script and follow the prompts. It will:
1. Open the exact Google Cloud pages you need in your browser
2. Wait for you to click the buttons
3. Automatically find and move your credentials file
4. Create and configure your Google Sheet
5. Update your .env file

Usage:  python setup_sheets.py
"""

import json
import os
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
DOWNLOADS_DIR = Path.home() / "Downloads"


def bold(text):
    return f"\033[1m{text}\033[0m"


def green(text):
    return f"\033[92m{text}\033[0m"


def yellow(text):
    return f"\033[93m{text}\033[0m"


def cyan(text):
    return f"\033[96m{text}\033[0m"


def banner():
    print()
    print(bold("=" * 55))
    print(bold("   Call Logger — Google Sheets Setup Wizard"))
    print(bold("=" * 55))
    print()


def wait_for_enter(message="Press ENTER when done..."):
    input(cyan(f"\n>>> {message} "))
    print()


def find_latest_json_in_downloads():
    """Find the most recently downloaded JSON file in Downloads."""
    json_files = list(DOWNLOADS_DIR.glob("*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda f: f.stat().st_mtime)


def step_1_create_project():
    print(bold("STEP 1 of 5: Create a Google Cloud Project"))
    print("-" * 45)
    print("I'm opening the Google Cloud project creation page.")
    print("Just fill in the project name as " + green("Call Logger") + " and click " + green("Create") + ".")
    print()
    webbrowser.open("https://console.cloud.google.com/projectcreate")
    wait_for_enter("Press ENTER after you've created the project...")

    project_id = input(cyan(">>> Paste the Project ID shown on the page (or just press ENTER to use 'call-logger'): ")).strip()
    if not project_id:
        project_id = "call-logger"
    print(green(f"  Using project: {project_id}"))
    return project_id


def step_2_enable_apis(project_id):
    print()
    print(bold("STEP 2 of 5: Enable Google Sheets & Drive APIs"))
    print("-" * 45)

    print("I'm opening the Sheets API page. Just click the blue " + green("ENABLE") + " button.")
    webbrowser.open(f"https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={project_id}")
    wait_for_enter("Press ENTER after clicking Enable on the Sheets API page...")

    print("Now I'm opening the Drive API page. Click " + green("ENABLE") + " again.")
    webbrowser.open(f"https://console.cloud.google.com/apis/library/drive.googleapis.com?project={project_id}")
    wait_for_enter("Press ENTER after clicking Enable on the Drive API page...")

    print(green("  APIs enabled!"))


def step_3_create_service_account(project_id):
    print()
    print(bold("STEP 3 of 5: Create a Service Account"))
    print("-" * 45)
    print("I'm opening the service account creation page.")
    print("Fill in:")
    print(f"  - Service account name: {green('call-logger')}")
    print(f"  - Click {green('Create and Continue')}")
    print(f"  - Skip the optional steps, just click {green('Done')}")
    print()
    webbrowser.open(f"https://console.cloud.google.com/iam-admin/serviceaccounts/create?project={project_id}")
    wait_for_enter("Press ENTER after creating the service account...")
    print(green("  Service account created!"))


def step_4_download_key(project_id):
    print()
    print(bold("STEP 4 of 5: Download the JSON Key"))
    print("-" * 45)
    print("I'm opening the service accounts page.")
    print("You should see your " + green("call-logger") + " service account listed.")
    print()
    print("Do this:")
    print(f"  1. Click the {green('call-logger')} service account email")
    print(f"  2. Click the {green('Keys')} tab at the top")
    print(f"  3. Click {green('Add Key')} > {green('Create new key')}")
    print(f"  4. Select {green('JSON')} and click {green('Create')}")
    print(f"  5. A file will download automatically")
    print()
    webbrowser.open(f"https://console.cloud.google.com/iam-admin/serviceaccounts?project={project_id}")

    # Record existing JSON files in Downloads before they download the new one
    existing_jsons = set(DOWNLOADS_DIR.glob("*.json"))

    wait_for_enter("Press ENTER after the JSON key file has downloaded...")

    # Try to find the newly downloaded JSON
    print("  Looking for the credentials file in your Downloads folder...")
    new_jsons = set(DOWNLOADS_DIR.glob("*.json")) - existing_jsons
    creds_file = None

    if new_jsons:
        creds_file = max(new_jsons, key=lambda f: f.stat().st_mtime)
    else:
        # Fall back to most recent JSON
        latest = find_latest_json_in_downloads()
        if latest and latest.stat().st_mtime > time.time() - 300:
            creds_file = latest

    if creds_file:
        print(green(f"  Found: {creds_file.name}"))
        # Move it to the project
        import shutil
        shutil.copy2(str(creds_file), str(CREDENTIALS_FILE))
        print(green(f"  Copied to: {CREDENTIALS_FILE}"))

        # Read service account email
        with open(CREDENTIALS_FILE) as f:
            creds_data = json.load(f)
        sa_email = creds_data.get("client_email", "")
        print(green(f"  Service account email: {sa_email}"))
        return sa_email
    else:
        print(yellow("  Couldn't auto-detect the file. Let me check..."))
        # Ask user to confirm
        manual_path = input(cyan(">>> Drag and drop the downloaded JSON file here (or paste the path): ")).strip().strip("'\"")
        if manual_path and Path(manual_path).exists():
            import shutil
            shutil.copy2(manual_path, str(CREDENTIALS_FILE))
            print(green(f"  Copied to: {CREDENTIALS_FILE}"))
            with open(CREDENTIALS_FILE) as f:
                creds_data = json.load(f)
            return creds_data.get("client_email", "")
        else:
            print(yellow("  Could not find credentials file. You'll need to manually place it at:"))
            print(f"  {CREDENTIALS_FILE}")
            return ""


def step_5_create_sheet(sa_email):
    print()
    print(bold("STEP 5 of 5: Create the Google Sheet"))
    print("-" * 45)
    print("I'm opening Google Sheets to create a new spreadsheet.")
    print()
    webbrowser.open("https://sheets.new")
    time.sleep(2)
    print("In the new sheet that just opened:")
    print(f"  1. Name it {green('Call Log')} (or whatever you like)")
    print(f"  2. Click {green('Share')} (top-right)")
    if sa_email:
        print(f"  3. Paste this email: {green(sa_email)}")
    else:
        print(f"  3. Paste the service account email from your credentials.json")
    print(f"  4. Give it {green('Editor')} access and click {green('Send')}")
    print()
    print("Then copy the " + green("Sheet ID") + " from the URL bar.")
    print("The URL looks like: docs.google.com/spreadsheets/d/" + green("SHEET_ID_IS_THIS_PART") + "/edit")
    print()

    sheet_id = input(cyan(">>> Paste the Sheet ID here: ")).strip()

    if sheet_id:
        # Update .env file
        update_env("CALL_LOG_SHEET_ID", sheet_id)
        print(green(f"  Sheet ID saved to .env!"))
    else:
        print(yellow("  No Sheet ID entered. You can add it later to your .env file as CALL_LOG_SHEET_ID=..."))

    return sheet_id


def update_env(key, value):
    """Add or update a key in the .env file."""
    if ENV_FILE.exists():
        content = ENV_FILE.read_text()
        lines = content.splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")
        ENV_FILE.write_text("\n".join(lines) + "\n")
    else:
        ENV_FILE.write_text(f"{key}={value}\n")


def test_connection(sheet_id):
    """Quick test to verify everything works."""
    print()
    print(bold("Testing the connection..."))
    print("-" * 45)
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        print(green(f"  Connected to: \"{spreadsheet.title}\""))
        print(green("  Everything is working!"))
        return True
    except Exception as e:
        print(yellow(f"  Connection test failed: {e}"))
        print(yellow("  Double-check that you shared the sheet with the service account email."))
        return False


def main():
    banner()

    if CREDENTIALS_FILE.exists():
        print(green("Credentials file already exists!"))
        with open(CREDENTIALS_FILE) as f:
            creds_data = json.load(f)
        sa_email = creds_data.get("client_email", "")
        print(f"  Service account: {sa_email}")
        print()
        skip = input(cyan(">>> Skip to Sheet setup? (y/n): ")).strip().lower()
        if skip == "y":
            sheet_id = step_5_create_sheet(sa_email)
            if sheet_id:
                test_connection(sheet_id)
            print()
            print(green(bold("Setup complete! Restart your Call Logger app to use Google Sheets export.")))
            return

    project_id = step_1_create_project()
    step_2_enable_apis(project_id)
    step_3_create_service_account(project_id)
    sa_email = step_4_download_key(project_id)
    sheet_id = step_5_create_sheet(sa_email)

    if sheet_id and CREDENTIALS_FILE.exists():
        test_connection(sheet_id)

    print()
    print(green(bold("=" * 55)))
    print(green(bold("   Setup complete!")))
    print(green(bold("=" * 55)))
    print()
    print("Your Call Logger app will now export weekly reports")
    print("to Google Sheets every Friday at 6 PM.")
    print()
    print("Restart the app to apply changes:")
    print(f"  cd {BASE_DIR} && python app.py")
    print()


if __name__ == "__main__":
    main()
