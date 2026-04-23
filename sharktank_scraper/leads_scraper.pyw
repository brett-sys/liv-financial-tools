"""Sharktank Leads Scraper — Tkinter GUI for scraping insurance leads."""

import csv
import io
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from tkinter import scrolledtext, messagebox

import requests

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://backend.socialinsuranceleads.com:3000"
SEARCH_ENDPOINT = "/v1/api/sharktank/leads/search"
LOGIN_ENDPOINT = "/v1/api/sharktank/login"

ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

CSV_FIELDS = [
    "Full Name", "First Name", "Last Name", "Date Of Birth", "Age",
    "Email", "Phone Number", "Street Address", "City", "State",
    "Zip Code", "Created Date", "Currently Insured", "Is Military",
    "Marital Status", "DUI", "Tobacco", "Major Medical Type",
    "Height Inches", "Weight Lbs", "Prescription Medications",
    "Coverage Type Option", "Requested Coverage Amount", "Hazards",
]

FIELD_MAP = {
    "Full Name": "fullName",
    "First Name": "first_name",
    "Last Name": "last_name",
    "Date Of Birth": "dateOfBirth",
    "Age": "age",
    "Email": "email",
    "Phone Number": "phoneNumber",
    "Street Address": "streetAddress",
    "City": "city",
    "State": "state",
    "Zip Code": "zipCode",
    "Created Date": "createdDate",
    "Currently Insured": "CurrentlyInsured",
    "Is Military": "IsMilitary",
    "Marital Status": "MaritalStatus",
    "DUI": "DUI",
    "Tobacco": "tobacco",
    "Major Medical Type": "MajorMedicalType",
    "Height Inches": "HeightInches",
    "Weight Lbs": "WeightLbs",
    "Prescription Medications": "PrescriptionMedications",
    "Coverage Type Option": "CoverageTypeOption",
    "Requested Coverage Amount": "RequestedCoverageAmount",
    "Hazards": "Hazards",
}

CONFIG_FILE = "leads_scraper_config.json"
LEADS_DIR = "Leads"
LOG_FILE = "scraper.log"

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_FOLDER_ID = os.getenv("LEAD_DRIVE_FOLDER_ID", "1qfo-He84pnSfA5qhtowJ_1FKL0rWdRqL")

PAGE_LIMIT = 500
BATCH_SAVE_SIZE = 20
RATE_LIMIT_SLEEP_MIN = 0.4   # random jitter range (seconds)
RATE_LIMIT_SLEEP_MAX = 1.6
BACKOFF_RATE_LIMITED = 5
BACKOFF_ERROR = 3
RETRY_COUNT = 3
RETRY_SLEEP = 5
FULL_MODE_THRESHOLD = 2000
POLL_INTERVAL_SECS = 300       # wait between cycles when no new leads
TOKEN_REFRESH_INTERVAL = 43200  # proactive token refresh every 12 hours

DEFAULT_DATE_FROM = "02/03/2026"

# Realistic browser User-Agent pool — rotated per request
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.8,es;q=0.5",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,fr;q=0.7",
    "en-US,en;q=0.9,de;q=0.7",
]

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
]


def parse_lead_date(raw):
    """Try common date formats and return a date object, or None."""
    if not raw:
        return None
    raw = str(raw).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], "%Y%m%d").date()
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def get_script_directory():
    fixed = os.path.expanduser("~/Desktop/python/sharktank_scraper")
    if os.path.isdir(fixed):
        return fixed
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resolve_csv_directory():
    base = get_script_directory()
    csv_dir = os.path.join(base, LEADS_DIR)
    os.makedirs(csv_dir, exist_ok=True)
    return csv_dir


def _config_path():
    return os.path.join(get_script_directory(), CONFIG_FILE)


def load_config():
    """Load full config; migrate/seed credentials on first run."""
    defaults = {
        "token": "",
        "email": "brett@fflliv.com",
        "password": "Password1234#!",
        "api_key": "df1559c16e1dcb8484ea9b7471ae771a423e0f57",
    }
    try:
        with open(_config_path(), "r") as f:
            data = json.load(f)
        changed = False
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
                changed = True
        if changed:
            save_config(data)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        save_config(defaults)
        return defaults


def save_config(data):
    try:
        with open(_config_path(), "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(_config_path(), 0o600)
    except OSError:
        pass


def load_saved_token():
    return load_config().get("token", "")


def save_token(token):
    cfg = load_config()
    cfg["token"] = token.strip()
    save_config(cfg)


def fetch_token_from_api(email=None, password=None, api_key=None):
    cfg = load_config()
    email = email or cfg["email"]
    password = password or cfg["password"]
    api_key = api_key or cfg["api_key"]
    url = f"{BASE_URL}{LOGIN_ENDPOINT}"
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json",
        "User-Agent": random.choice(USER_AGENTS),
    }
    resp = requests.post(url, json={"user": email, "pass": password}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("user", {}).get("token", "")


def _find_credentials():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    for candidate in [
        os.path.join(script_dir, "credentials.json"),
        os.path.join(project_root, "call_logger", "credentials.json"),
        os.path.join(project_root, "agent_toolkit", "credentials.json"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return None


def macos_notify(title, message):
    """Fire a native macOS notification banner (silent fail on non-Mac)."""
    try:
        safe_msg = message.replace('"', "'")
        safe_title = title.replace('"', "'")
        subprocess.run(
            ["osascript", "-e", f'display notification "{safe_msg}" with title "{safe_title}"'],
            timeout=5, capture_output=True,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LeadsScraper — Core Engine
# ---------------------------------------------------------------------------


class LeadsScraper:
    def __init__(self, auth_token, callbacks, csv_dir, date_from=None, date_to=None,
                 max_workers=5, upload_to_drive=False):
        self.auth_token = auth_token
        self.csv_dir = csv_dir
        self.date_from = date_from
        self.date_to = date_to
        self.max_workers = max_workers
        self.upload_to_drive = upload_to_drive

        self._stop = threading.Event()
        self._token_lock = threading.Lock()
        self._drive_service = None
        self._drive_lock = threading.Lock()
        self._csv_lock = threading.Lock()         # guard merged CSV writes
        self._seen_lock = threading.Lock()        # guard dedup set
        self._seen_phones: set = set()            # phone numbers already written today
        self._refresh_stop = threading.Event()   # signals background refresh thread to exit

        self.on_log = callbacks.get("on_log", lambda msg, color=None: None)
        self.on_progress = callbacks.get("on_progress", lambda state, count: None)
        self.on_state_done = callbacks.get("on_state_done", lambda state, count: None)
        self.on_cycle_done = callbacks.get("on_cycle_done", lambda: None)

        if self.upload_to_drive:
            self._init_drive()

    # -- Google Drive -------------------------------------------------------

    def _init_drive(self):
        if not GDRIVE_AVAILABLE:
            self.on_log("Google Drive libraries not installed — upload disabled", "warning")
            self.upload_to_drive = False
            return
        creds_path = _find_credentials()
        if not creds_path:
            self.on_log("No credentials.json found — Drive upload disabled", "warning")
            self.upload_to_drive = False
            return
        try:
            creds = Credentials.from_service_account_file(creds_path, scopes=DRIVE_SCOPES)
            self._drive_service = build("drive", "v3", credentials=creds)
            self.on_log("Google Drive connected", "success")
        except Exception as exc:
            self.on_log(f"Drive auth failed: {exc} — upload disabled", "error")
            self.upload_to_drive = False

    def _find_drive_file(self, filename):
        with self._drive_lock:
            resp = self._drive_service.files().list(
                q=f"'{DRIVE_FOLDER_ID}' in parents and name='{filename}' and trashed=false",
                fields="files(id, name)",
                pageSize=1,
            ).execute()
        files = resp.get("files", [])
        return files[0]["id"] if files else None

    def _upload_to_drive(self, local_path):
        if not self.upload_to_drive or not self._drive_service:
            return
        filename = os.path.basename(local_path)
        try:
            with open(local_path, "rb") as f:
                media = MediaIoBaseUpload(f, mimetype="text/csv", resumable=True)
                existing_id = self._find_drive_file(filename)
                if existing_id:
                    with self._drive_lock:
                        self._drive_service.files().update(
                            fileId=existing_id, media_body=media,
                        ).execute()
                    self.on_log(f"  ↑ Drive: updated {filename}", "success")
                else:
                    metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}
                    with self._drive_lock:
                        self._drive_service.files().create(
                            body=metadata, media_body=media, fields="id",
                        ).execute()
                    self.on_log(f"  ↑ Drive: uploaded {filename}", "success")
        except Exception as exc:
            self.on_log(f"  ↑ Drive upload failed ({filename}): {exc}", "error")

    # -- File helpers -------------------------------------------------------

    def _csv_path(self, state, recent=False):
        today = datetime.now().strftime("%Y-%m-%d")
        suffix = "_recent" if recent else ""
        return os.path.join(self.csv_dir, f"leads_{state}_{today}{suffix}.csv")

    def _merged_csv_path(self):
        """Daily mode writes a single merged file instead of 50 per-state files."""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.csv_dir, f"leads_all_{today}.csv")

    def _count_leads_in_file(self, path):
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                return max(sum(1 for _ in f) - 1, 0)
        except OSError:
            return 0

    def _existing_lead_count(self, state):
        today = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(self.csv_dir, f"leads_{state}_{today}.csv")
        return self._count_leads_in_file(path)

    def _load_seen_phones(self, path):
        """Return set of phone numbers already present in a CSV file."""
        phones = set()
        if not os.path.exists(path):
            return phones
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p = str(row.get("Phone Number", "")).strip()
                    if p:
                        phones.add(p)
        except OSError:
            pass
        return phones

    # -- State filtering ----------------------------------------------------

    def get_states_with_less_than_2000(self):
        return [s for s in ALL_STATES if self._existing_lead_count(s) < FULL_MODE_THRESHOLD]

    def get_states_without_recent_file(self):
        return [s for s in ALL_STATES if not os.path.exists(self._csv_path(s, recent=True))]

    def filter_states_with_2000_plus(self, states):
        return [s for s in states if self._existing_lead_count(s) >= FULL_MODE_THRESHOLD]

    # -- API ----------------------------------------------------------------

    def _random_headers(self):
        """Build randomised request headers to avoid bot fingerprinting."""
        cfg = load_config()
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": random.choice(ACCEPT_LANGUAGES),
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def _fetch_page(self, state_code, page):
        url = (
            f"{BASE_URL}{SEARCH_ENDPOINT}"
            f"?state={state_code}&page={page}&limit={PAGE_LIMIT}"
        )
        resp = requests.get(url, headers=self._random_headers(), timeout=90)
        return resp

    # -- Date filtering -----------------------------------------------------

    def _filter_by_date(self, leads):
        if not self.date_from and not self.date_to:
            return leads, False
        filtered = []
        dated_count = 0
        before_count = 0
        for lead in leads:
            d = parse_lead_date(lead.get("createdDate"))
            if d is None:
                filtered.append(lead)
                continue
            dated_count += 1
            if self.date_from and d < self.date_from:
                before_count += 1
                continue
            if self.date_to and d > self.date_to:
                continue
            filtered.append(lead)
        all_before = dated_count > 0 and before_count == dated_count
        return filtered, all_before

    # -- CSV writing --------------------------------------------------------

    def save_leads_to_csv(self, state, leads, recent=False, daily=False):
        """Write leads to CSV, skipping duplicates by phone number."""
        if daily:
            path = self._merged_csv_path()
            lock = self._csv_lock
        else:
            path = self._csv_path(state, recent)
            lock = self._csv_lock

        with lock:
            file_exists = os.path.exists(path) and os.path.getsize(path) > 0
            new_leads = []
            for lead in leads:
                phone = str(lead.get("phoneNumber", "")).strip()
                if not phone:
                    new_leads.append(lead)
                    continue
                with self._seen_lock:
                    if phone in self._seen_phones:
                        continue
                    self._seen_phones.add(phone)
                new_leads.append(lead)

            if not new_leads:
                return path

            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                for lead in new_leads:
                    row = {csv_field: lead.get(api_key, "") for csv_field, api_key in FIELD_MAP.items()}
                    writer.writerow(row)

        return path

    # -- Token management ---------------------------------------------------

    def _refresh_token(self, tag):
        """Thread-safe token refresh with retries. Returns True on success."""
        with self._token_lock:
            self.on_log(f"  [{tag}] Token expired (401). Re-logging in…", "warning")
            for attempt in range(1, RETRY_COUNT + 1):
                if self._stop.is_set():
                    return False
                try:
                    new_token = fetch_token_from_api()
                    if new_token:
                        self.auth_token = new_token
                        save_token(new_token)
                        self.on_log(f"  [{tag}] Token refreshed.", "success")
                        return True
                except Exception as exc:
                    self.on_log(f"  [{tag}] Re-login attempt {attempt}/{RETRY_COUNT} failed: {exc}", "warning")
                    if attempt < RETRY_COUNT:
                        time.sleep(RETRY_SLEEP)
            self.on_log(f"  [{tag}] Re-login failed after {RETRY_COUNT} attempts. Stopping.", "error")
            self._stop.set()
            return False

    def _token_refresh_loop(self):
        """Background thread: proactively refresh token every 12 hours."""
        while not self._refresh_stop.wait(timeout=TOKEN_REFRESH_INTERVAL):
            if self._stop.is_set():
                break
            try:
                new_token = fetch_token_from_api()
                if new_token:
                    with self._token_lock:
                        self.auth_token = new_token
                        save_token(new_token)
                    self.on_log("  [AUTH] Proactive token refresh succeeded.", "dim")
            except Exception as exc:
                self.on_log(f"  [AUTH] Proactive token refresh failed: {exc}", "warning")

    # -- Single state scrape ------------------------------------------------

    def scrape_state(self, state_code, recent_mode=False, max_leads=None, daily=False):
        if self._stop.is_set():
            return 0
        page = 1
        total = 0
        batch = []
        consecutive_empty = 0
        tag = state_code

        self.on_log(f"  [{tag}] Starting {'daily' if daily else 'recent' if recent_mode else 'full'} scrape", "info")

        # Seed dedup set from today's existing file for this state/mode
        with self._seen_lock:
            existing_path = self._merged_csv_path() if daily else self._csv_path(state_code, recent_mode)
            if not self._seen_phones:
                self._seen_phones.update(self._load_seen_phones(existing_path))

        while not self._stop.is_set():
            if max_leads and total >= max_leads:
                self.on_log(f"  [{tag}] Hit limit of {max_leads}", "success")
                break

            try:
                resp = self._fetch_page(state_code, page)
            except requests.RequestException as exc:
                self.on_log(f"  [{tag}] Request error p{page}: {exc}", "warning")
                retried = self._retry_on_error(tag, state_code, page)
                if retried is None:
                    break
                resp = retried

            if resp.status_code == 401:
                if not self._refresh_token(tag):
                    break
                continue

            if resp.status_code == 429:
                self.on_log(f"  [{tag}] Rate limited (429). Backing off…", "warning")
                time.sleep(random.uniform(5, 15))
                continue

            if resp.status_code != 200:
                retried = self._retry_on_error(tag, state_code, page)
                if retried is None:
                    break
                if retried.status_code != 200:
                    self.on_log(f"  [{tag}] Failed after retries p{page}", "error")
                    break
                resp = retried

            try:
                data = resp.json()
            except ValueError:
                self.on_log(f"  [{tag}] Invalid JSON p{page}", "error")
                break

            rows = data.get("leads", {}).get("rows", [])
            raw_leads = [row.get("body", {}) for row in rows if row.get("body")]
            pre_filter = len(raw_leads)
            leads, all_before = self._filter_by_date(raw_leads)

            if all_before:
                self.on_log(f"  [{tag}] All {pre_filter} leads on p{page} before date range — stopping early", "dim")
                break

            if pre_filter > 0 and not leads:
                self.on_log(f"  [{tag}] p{page}: {pre_filter} filtered out by date", "dim")

            if not leads:
                consecutive_empty += 1
                if consecutive_empty >= RETRY_COUNT:
                    self.on_log(f"  [{tag}] No more leads (p{page})", "dim")
                    break
                time.sleep(RETRY_SLEEP)
                page += 1
                continue

            consecutive_empty = 0
            batch.extend(leads)
            total += len(leads)

            if len(batch) >= BATCH_SAVE_SIZE:
                self.save_leads_to_csv(state_code, batch, recent=recent_mode, daily=daily)
                batch = []

            self.on_log(f"  [{tag}] p{page}: +{len(leads)} leads (total: {total})", "success")
            self.on_progress(state_code, total)

            page += 1
            time.sleep(random.uniform(RATE_LIMIT_SLEEP_MIN, RATE_LIMIT_SLEEP_MAX))

        if batch:
            self.save_leads_to_csv(state_code, batch, recent=recent_mode, daily=daily)

        if total > 0 and self.upload_to_drive:
            path = self._merged_csv_path() if daily else self._csv_path(state_code, recent=recent_mode)
            self._upload_to_drive(path)

        self.on_state_done(state_code, total)
        return total

    def _retry_on_error(self, tag, state_code, page):
        for attempt in range(1, RETRY_COUNT + 1):
            if self._stop.is_set():
                return None
            self.on_log(f"  [{tag}] Retry {attempt}/{RETRY_COUNT}", "warning")
            time.sleep(RETRY_SLEEP)
            try:
                resp = self._fetch_page(state_code, page)
                if resp.status_code == 200:
                    return resp
            except requests.RequestException:
                continue
        return None

    # -- Orchestrator loops -------------------------------------------------

    def start_scraping(self, states, mode="full", max_leads=None):
        self._stop.clear()
        self._refresh_stop.clear()
        cycle = 0
        recent = mode in ("recent", "daily")
        daily = mode == "daily"

        # Start background token refresh thread
        refresh_thread = threading.Thread(target=self._token_refresh_loop, daemon=True)
        refresh_thread.start()

        # Small random startup delay to vary the daily run fingerprint
        if daily:
            time.sleep(random.uniform(3, 20))

        while not self._stop.is_set():
            cycle += 1

            if daily:
                today = date.today()
                self.date_from = today
                self.date_to = today
                # Reset seen phones at midnight for the new day
                with self._seen_lock:
                    self._seen_phones.clear()
                    merged_path = self._merged_csv_path()
                    self._seen_phones.update(self._load_seen_phones(merged_path))

            self.on_log(f"\n{'═' * 50}", "dim")
            self.on_log(f"  CYCLE {cycle} — {mode.upper()} MODE  ({self.max_workers} workers)", "info")
            self.on_log(f"{'═' * 50}", "dim")

            if mode == "full":
                work = self.get_states_with_less_than_2000()
                skipped = [s for s in states if s not in work]
                if skipped:
                    self.on_log(f"  Skipping {len(skipped)} state(s) with {FULL_MODE_THRESHOLD}+ leads", "dim")
            else:
                work = list(states)

            if not work:
                self.on_log("  All states complete. Waiting 60s before re-check…", "success")
                for _ in range(60):
                    if self._stop.is_set():
                        break
                    time.sleep(1)
                continue

            if daily:
                self.on_log(f"  Date: {self.date_from.strftime('%m/%d/%Y')} → merged CSV: leads_all_{self.date_from}.csv", "info")
            else:
                random.shuffle(work)
            self.on_log(f"  Queued {len(work)} state(s): {', '.join(work)}", "info")

            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {}
                for state in work:
                    if self._stop.is_set():
                        break
                    f = pool.submit(self.scrape_state, state,
                                    recent_mode=recent, max_leads=max_leads, daily=daily)
                    futures[f] = state
                cycle_total = 0
                for f in as_completed(futures):
                    if self._stop.is_set():
                        pool.shutdown(wait=False, cancel_futures=True)
                        break
                    try:
                        cycle_total += f.result()
                    except Exception as exc:
                        self.on_log(f"  [{futures[f]}] Error: {exc}", "error")

            self.on_cycle_done()

            if self._stop.is_set():
                break

            if daily:
                secs = self._seconds_until_midnight()
                h, rem = divmod(secs, 3600)
                m = rem // 60
                msg = f"Daily run complete — {cycle_total:,} new leads. Next run at midnight ({h}h {m}m)."
                self.on_log(f"  {msg}", "success")
                macos_notify("🦈 Sharktank Scraper", msg)
                for _ in range(secs):
                    if self._stop.is_set():
                        break
                    time.sleep(1)
            elif cycle_total == 0:
                wait_min = POLL_INTERVAL_SECS // 60
                self.on_log(f"  No new leads this cycle. Waiting {wait_min}m before next check…", "dim")
                for _ in range(POLL_INTERVAL_SECS):
                    if self._stop.is_set():
                        break
                    time.sleep(1)

        self._refresh_stop.set()
        self.on_log("\n⏹ Scraping stopped.", "warning")

    def stop_scraping(self):
        self._stop.set()
        self._refresh_stop.set()

    def _seconds_until_midnight(self):
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return max(int((midnight - now).total_seconds()), 1)


# ---------------------------------------------------------------------------
# LeadsScraperGUI — Tkinter UI
# ---------------------------------------------------------------------------


class LeadsScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sharktank Leads Scraper")
        self.root.geometry("1020x720")
        self.root.minsize(900, 600)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lumberjack_logo.png")
        if os.path.exists(logo_path):
            self._app_icon = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(True, self._app_icon)

        self.scraper = None
        self.scrape_thread = None
        self.auth_token = load_saved_token()
        self.csv_dir = resolve_csv_directory()
        self._token_save_job = None
        self.session_stats = {}
        self.state_vars = {}

        # Open persistent log file
        log_path = os.path.join(self.csv_dir, LOG_FILE)
        try:
            self._log_fh = open(log_path, "a", encoding="utf-8", buffering=1)
        except OSError:
            self._log_fh = None

        self._setup_ui()
        self._load_token_into_ui()
        if not self.auth_token:
            self.root.after(500, self._auto_login)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self._log_fh:
            try:
                self._log_fh.close()
            except OSError:
                pass
        self.root.destroy()

    # -- UI construction ----------------------------------------------------

    def _setup_ui(self):
        self.root.configure(bg="#1e1e2e")

        top = tk.Frame(self.root, bg="#1e1e2e", pady=6, padx=12)
        top.pack(fill=tk.X)
        tk.Label(
            top, text="🦈 Sharktank Leads Scraper",
            font=("Helvetica", 16, "bold"), fg="#89b4fa", bg="#1e1e2e",
        ).pack(side=tk.LEFT)

        body = tk.Frame(self.root, bg="#1e1e2e")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left = tk.Frame(body, bg="#313244", width=280, relief=tk.FLAT)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg="#1e1e2e")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_token_panel(left)
        self._build_state_panel(left)
        self._build_controls(left)
        self._build_log_panel(right)
        self._build_summary_panel(right)

    def _build_token_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" Auth Token ", font=("Helvetica", 10, "bold"),
            fg="#cdd6f4", bg="#313244", bd=1, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.token_text = tk.Text(
            frame, height=3, wrap=tk.WORD, font=("Consolas", 9),
            bg="#45475a", fg="#a6e3a1", insertbackground="#a6e3a1",
            relief=tk.FLAT, bd=4,
        )
        self.token_text.pack(fill=tk.X, padx=4, pady=(4, 2))
        self.token_text.bind("<KeyRelease>", self._on_token_change)

        self.btn_login = tk.Button(
            frame, text="Refresh Token", font=("Helvetica", 9, "bold"),
            bg="#f9e2af", fg="#1e1e2e", activebackground="#f5c2e7",
            relief=tk.FLAT, padx=6, pady=2, command=lambda: self._auto_login(),
        )
        self.btn_login.pack(fill=tk.X, padx=4, pady=(0, 4))

    def _build_state_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" States ", font=("Helvetica", 10, "bold"),
            fg="#cdd6f4", bg="#313244", bd=1, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.all_states_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame, text="All States", variable=self.all_states_var,
            font=("Helvetica", 10, "bold"), fg="#f9e2af", bg="#313244",
            selectcolor="#45475a", activebackground="#313244",
            command=self._toggle_all_states,
        ).pack(anchor=tk.W, padx=6, pady=(4, 2))

        canvas = tk.Canvas(frame, bg="#313244", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="#313244")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        cols = 3
        for i, state in enumerate(ALL_STATES):
            var = tk.BooleanVar(value=True)
            self.state_vars[state] = var
            cb = tk.Checkbutton(
                inner, text=state, variable=var,
                font=("Consolas", 9), fg="#cdd6f4", bg="#313244",
                selectcolor="#45475a", activebackground="#313244",
            )
            cb.grid(row=i // cols, column=i % cols, sticky=tk.W, padx=2)

    def _build_controls(self, parent):
        frame = tk.Frame(parent, bg="#313244")
        frame.pack(fill=tk.X, padx=8, pady=(4, 8))

        date_frame = tk.LabelFrame(
            frame, text=" Date Range (MM/DD/YYYY) ", font=("Helvetica", 9, "bold"),
            fg="#cdd6f4", bg="#313244", bd=1, relief=tk.GROOVE,
        )
        date_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        row_from = tk.Frame(date_frame, bg="#313244")
        row_from.pack(fill=tk.X, padx=4, pady=(4, 2))
        tk.Label(row_from, text="From:", font=("Helvetica", 9), fg="#cdd6f4", bg="#313244", width=5, anchor=tk.W).pack(side=tk.LEFT)
        self.date_from_var = tk.StringVar(value=DEFAULT_DATE_FROM)
        tk.Entry(row_from, textvariable=self.date_from_var, font=("Consolas", 10), bg="#45475a", fg="#a6e3a1",
                 insertbackground="#a6e3a1", relief=tk.FLAT, bd=3, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row_to = tk.Frame(date_frame, bg="#313244")
        row_to.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(row_to, text="To:", font=("Helvetica", 9), fg="#cdd6f4", bg="#313244", width=5, anchor=tk.W).pack(side=tk.LEFT)
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y"))
        tk.Entry(row_to, textvariable=self.date_to_var, font=("Consolas", 10), bg="#45475a", fg="#a6e3a1",
                 insertbackground="#a6e3a1", relief=tk.FLAT, bd=3, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(frame, text="Workers (parallel states):", font=("Helvetica", 9), fg="#cdd6f4", bg="#313244").pack(anchor=tk.W, padx=4)

        self.workers_var = tk.StringVar(value="5")
        workers_frame = tk.Frame(frame, bg="#313244")
        workers_frame.pack(fill=tk.X, padx=4, pady=(0, 6))
        for val in ("1", "3", "5", "8"):
            tk.Radiobutton(
                workers_frame, text=val, variable=self.workers_var, value=val,
                font=("Consolas", 9), fg="#cdd6f4", bg="#313244",
                selectcolor="#45475a", activebackground="#313244",
            ).pack(side=tk.LEFT, padx=2)

        tk.Label(frame, text="Recent limit:", font=("Helvetica", 9), fg="#cdd6f4", bg="#313244").pack(anchor=tk.W, padx=4)

        self.limit_var = tk.StringVar(value="500")
        limit_frame = tk.Frame(frame, bg="#313244")
        limit_frame.pack(fill=tk.X, padx=4, pady=(0, 6))
        for val in ("250", "500", "750", "1500"):
            tk.Radiobutton(
                limit_frame, text=val, variable=self.limit_var, value=val,
                font=("Consolas", 9), fg="#cdd6f4", bg="#313244",
                selectcolor="#45475a", activebackground="#313244",
            ).pack(side=tk.LEFT, padx=2)

        self.drive_var = tk.BooleanVar(value=GDRIVE_AVAILABLE)
        drive_cb = tk.Checkbutton(
            frame, text="Upload to Google Drive", variable=self.drive_var,
            font=("Helvetica", 9, "bold"), fg="#89b4fa", bg="#313244",
            selectcolor="#45475a", activebackground="#313244",
            disabledforeground="#6c7086",
        )
        drive_cb.pack(anchor=tk.W, padx=6, pady=(4, 6))
        if not GDRIVE_AVAILABLE:
            drive_cb.configure(state=tk.DISABLED)
            self.drive_var.set(False)

        btn_frame = tk.Frame(frame, bg="#313244")
        btn_frame.pack(fill=tk.X, padx=4, pady=2)

        self.btn_full = tk.Button(
            btn_frame, text="▶ Start Full", font=("Helvetica", 10, "bold"),
            bg="#a6e3a1", fg="#1e1e2e", activebackground="#94e2d5",
            relief=tk.FLAT, padx=10, pady=4, command=self._start_full,
        )
        self.btn_full.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_recent = tk.Button(
            btn_frame, text="▶ Start Recent", font=("Helvetica", 10, "bold"),
            bg="#89b4fa", fg="#1e1e2e", activebackground="#74c7ec",
            relief=tk.FLAT, padx=10, pady=4, command=self._start_recent,
        )
        self.btn_recent.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_daily = tk.Button(
            frame, text="📅 Auto Daily (All States)", font=("Helvetica", 10, "bold"),
            bg="#cba6f7", fg="#1e1e2e", activebackground="#b4befe",
            relief=tk.FLAT, padx=10, pady=4, command=self._start_daily,
        )
        self.btn_daily.pack(fill=tk.X, padx=4, pady=(4, 0))

        self.btn_stop = tk.Button(
            frame, text="⏹ Stop", font=("Helvetica", 10, "bold"),
            bg="#f38ba8", fg="#1e1e2e", activebackground="#eba0ac",
            relief=tk.FLAT, padx=10, pady=4, state=tk.DISABLED,
            command=self._stop,
        )
        self.btn_stop.pack(fill=tk.X, padx=4, pady=(4, 0))

    def _build_log_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" Log ", font=("Helvetica", 10, "bold"),
            fg="#cdd6f4", bg="#1e1e2e", bd=1, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.log_console = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, bd=6, state=tk.DISABLED,
        )
        self.log_console.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.log_console.tag_configure("info", foreground="#89b4fa")
        self.log_console.tag_configure("success", foreground="#a6e3a1")
        self.log_console.tag_configure("warning", foreground="#f9e2af")
        self.log_console.tag_configure("error", foreground="#f38ba8")
        self.log_console.tag_configure("dim", foreground="#6c7086")

    def _build_summary_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" Session Summary ", font=("Helvetica", 10, "bold"),
            fg="#cdd6f4", bg="#1e1e2e", bd=1, relief=tk.GROOVE,
        )
        frame.pack(fill=tk.X)

        self.summary_var = tk.StringVar(value="No data yet")
        tk.Label(
            frame, textvariable=self.summary_var,
            font=("Consolas", 10), fg="#a6e3a1", bg="#1e1e2e",
            anchor=tk.W, justify=tk.LEFT,
        ).pack(fill=tk.X, padx=8, pady=6)

    # -- Token management ---------------------------------------------------

    def _load_token_into_ui(self):
        if self.auth_token:
            self.token_text.insert("1.0", self.auth_token)

    def _on_token_change(self, event=None):
        if self._token_save_job:
            self.root.after_cancel(self._token_save_job)
        self._token_save_job = self.root.after(2000, self._save_token_from_ui)

    def _save_token_from_ui(self):
        token = self.token_text.get("1.0", tk.END).strip()
        if token:
            self.auth_token = token
            save_token(token)
            self._log("Token saved.", "dim")

    def _auto_login(self):
        self._log("Fetching fresh token via login…", "info")
        try:
            token = fetch_token_from_api()
            if token:
                self.auth_token = token
                save_token(token)
                self.token_text.configure(state=tk.NORMAL)
                self.token_text.delete("1.0", tk.END)
                self.token_text.insert("1.0", token)
                self._log("Token refreshed.", "success")
                return True
            else:
                self._log("Login succeeded but no token returned.", "error")
        except Exception as exc:
            self._log(f"Auto-login failed: {exc}", "error")
        return False

    # -- Date parsing -------------------------------------------------------

    def _parse_date_fields(self):
        d_from = d_to = None
        raw_from = self.date_from_var.get().strip()
        raw_to = self.date_to_var.get().strip()
        if raw_from:
            try:
                d_from = datetime.strptime(raw_from, "%m/%d/%Y").date()
            except ValueError:
                messagebox.showwarning("Bad Date", f"Invalid From date: {raw_from}\nUse MM/DD/YYYY")
                return None, None
        if raw_to:
            try:
                d_to = datetime.strptime(raw_to, "%m/%d/%Y").date()
            except ValueError:
                messagebox.showwarning("Bad Date", f"Invalid To date: {raw_to}\nUse MM/DD/YYYY")
                return None, None
        return d_from, d_to

    # -- State selection ----------------------------------------------------

    def _toggle_all_states(self):
        val = self.all_states_var.get()
        for var in self.state_vars.values():
            var.set(val)

    def _selected_states(self):
        if self.all_states_var.get():
            return list(ALL_STATES)
        return [s for s, v in self.state_vars.items() if v.get()]

    # -- Logging ------------------------------------------------------------

    def _log(self, message, color=None):
        def _insert():
            self.log_console.configure(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            tag = color if color else ""
            line = f"[{ts}] {message}\n"
            self.log_console.insert(tk.END, line, tag)
            self.log_console.see(tk.END)
            self.log_console.configure(state=tk.DISABLED)
            # Write to log file
            if self._log_fh:
                try:
                    self._log_fh.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
                except OSError:
                    pass

        if threading.current_thread() is threading.main_thread():
            _insert()
        else:
            self.root.after(0, _insert)

    def _update_summary(self):
        if not self.session_stats:
            return
        total = sum(self.session_stats.values())
        states_done = len(self.session_stats)
        lines = [f"States scraped: {states_done}  |  Total leads: {total:,}"]
        top = sorted(self.session_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("Top: " + ", ".join(f"{s}:{c}" for s, c in top))
        self.summary_var.set("\n".join(lines))

    # -- Scraper callbacks --------------------------------------------------

    def _on_progress(self, state, count):
        pass

    def _on_state_done(self, state, count):
        self.session_stats[state] = self.session_stats.get(state, 0) + count
        self.root.after(0, self._update_summary)

    def _on_cycle_done(self):
        self._log("Cycle complete. Restarting…", "info")

    # -- Start / Stop -------------------------------------------------------

    def _set_running(self, running):
        state_run = tk.DISABLED if running else tk.NORMAL
        state_stop = tk.NORMAL if running else tk.DISABLED
        self.btn_full.configure(state=state_run)
        self.btn_recent.configure(state=state_run)
        self.btn_daily.configure(state=state_run)
        self.btn_stop.configure(state=state_stop)
        self.token_text.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _make_callbacks(self):
        return {
            "on_log": self._log,
            "on_progress": self._on_progress,
            "on_state_done": self._on_state_done,
            "on_cycle_done": self._on_cycle_done,
        }

    def _start_full(self):
        self._save_token_from_ui()
        if not self.auth_token:
            messagebox.showwarning("No Token", "Paste a JWT token before starting.")
            return
        states = self._selected_states()
        if not states:
            messagebox.showwarning("No States", "Select at least one state.")
            return
        d_from, d_to = self._parse_date_fields()
        if d_from is None and self.date_from_var.get().strip():
            return
        self.session_stats = {}
        self._set_running(True)
        date_msg = f" ({d_from} → {d_to or 'now'})" if d_from or d_to else ""
        self._log(f"Starting FULL scrape{date_msg}…", "info")
        workers = int(self.workers_var.get())
        self.scraper = LeadsScraper(
            self.auth_token, self._make_callbacks(), self.csv_dir,
            date_from=d_from, date_to=d_to, max_workers=workers,
            upload_to_drive=self.drive_var.get(),
        )
        self.scrape_thread = threading.Thread(
            target=self._run_scraper, args=(states, "full", None), daemon=True,
        )
        self.scrape_thread.start()

    def _start_recent(self):
        self._save_token_from_ui()
        if not self.auth_token:
            messagebox.showwarning("No Token", "Paste a JWT token before starting.")
            return
        states = self._selected_states()
        if not states:
            messagebox.showwarning("No States", "Select at least one state.")
            return
        d_from, d_to = self._parse_date_fields()
        if d_from is None and self.date_from_var.get().strip():
            return
        max_leads = int(self.limit_var.get())
        self.session_stats = {}
        self._set_running(True)
        date_msg = f" ({d_from} → {d_to or 'now'})" if d_from or d_to else ""
        self._log(f"Starting RECENT scrape (limit: {max_leads}){date_msg}…", "info")
        workers = int(self.workers_var.get())
        self.scraper = LeadsScraper(
            self.auth_token, self._make_callbacks(), self.csv_dir,
            date_from=d_from, date_to=d_to, max_workers=workers,
            upload_to_drive=self.drive_var.get(),
        )
        self.scrape_thread = threading.Thread(
            target=self._run_scraper, args=(states, "recent", max_leads), daemon=True,
        )
        self.scrape_thread.start()

    def _start_daily(self):
        self._save_token_from_ui()
        if not self.auth_token:
            messagebox.showwarning("No Token", "Paste a JWT token before starting.")
            return
        self.session_stats = {}
        self._set_running(True)
        workers = int(self.workers_var.get())
        today = date.today().strftime("%m/%d/%Y")
        self._log(f"Starting AUTO DAILY scrape — all 50 states, today's leads ({today}), runs daily at midnight…", "info")
        self.scraper = LeadsScraper(
            self.auth_token, self._make_callbacks(), self.csv_dir,
            max_workers=workers, upload_to_drive=self.drive_var.get(),
        )
        self.scrape_thread = threading.Thread(
            target=self._run_scraper, args=(list(ALL_STATES), "daily", None), daemon=True,
        )
        self.scrape_thread.start()

    def _run_scraper(self, states, mode, max_leads):
        try:
            self.scraper.start_scraping(states, mode=mode, max_leads=max_leads)
        except Exception as exc:
            self._log(f"Fatal error: {exc}", "error")
        finally:
            self.root.after(0, lambda: self._set_running(False))

    def _stop(self):
        if self.scraper and not self.scraper._stop.is_set():
            self.scraper.stop_scraping()
            self._log("Stop requested — finishing current page…", "warning")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main():
    root = tk.Tk()
    LeadsScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
