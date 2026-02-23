"""Sharktank Leads Scraper — Tkinter GUI for scraping insurance leads."""

import csv
import json
import os
import random
import re
import sys
import threading
import time
import tkinter as tk
from datetime import datetime, date
from tkinter import scrolledtext, messagebox

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://backend.socialinsuranceleads.com:3000"
API_PREFIX = "/v1/api"
SEARCH_ENDPOINT = "/v1/api/sharktank/leads/search"
LOGIN_ENDPOINT = "/v1/api/sharktank/login"
API_KEY = "df1559c16e1dcb8484ea9b7471ae771a423e0f57"

DEFAULT_TOKEN = ""
DEFAULT_EMAIL = "brett@fflliv.com"
DEFAULT_PASSWORD = "Password1234#!"

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
PAGE_LIMIT = 500
BATCH_SAVE_SIZE = 20
RATE_LIMIT_SLEEP = 2
RETRY_COUNT = 3
RETRY_SLEEP = 10
FULL_MODE_THRESHOLD = 2000

DEFAULT_DATE_FROM = "02/03/2026"

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
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resolve_csv_directory():
    base = get_script_directory()
    csv_dir = os.path.join(base, LEADS_DIR)
    os.makedirs(csv_dir, exist_ok=True)
    return csv_dir


def load_saved_token():
    config_path = os.path.join(get_script_directory(), CONFIG_FILE)
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get("token", DEFAULT_TOKEN)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_TOKEN


def save_token(token):
    config_path = os.path.join(get_script_directory(), CONFIG_FILE)
    try:
        with open(config_path, "w") as f:
            json.dump({"token": token.strip()}, f, indent=2)
    except OSError:
        pass


def fetch_token_from_api(email, password):
    url = f"{BASE_URL}{LOGIN_ENDPOINT}"
    headers = {
        "Authorization": f"ApiKey {API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, json={"user": email, "pass": password}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("user", {}).get("token", "")


# ---------------------------------------------------------------------------
# LeadsScraper — Core Engine
# ---------------------------------------------------------------------------


class LeadsScraper:
    def __init__(self, auth_token, callbacks, csv_dir, date_from=None, date_to=None):
        self.auth_token = auth_token
        self.csv_dir = csv_dir
        self.date_from = date_from
        self.date_to = date_to
        self._stop = threading.Event()

        self.on_log = callbacks.get("on_log", lambda msg, color=None: None)
        self.on_progress = callbacks.get("on_progress", lambda state, count: None)
        self.on_state_done = callbacks.get("on_state_done", lambda state, count: None)
        self.on_cycle_done = callbacks.get("on_cycle_done", lambda: None)

    # -- File helpers -------------------------------------------------------

    def _csv_path(self, state, recent=False):
        today = datetime.now().strftime("%Y-%m-%d")
        suffix = "_recent" if recent else ""
        return os.path.join(self.csv_dir, f"leads_{state}_{today}{suffix}.csv")

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
        pattern = f"leads_{state}_{today}.csv"
        path = os.path.join(self.csv_dir, pattern)
        return self._count_leads_in_file(path)

    # -- State filtering ----------------------------------------------------

    def get_states_with_less_than_2000(self):
        return [s for s in ALL_STATES if self._existing_lead_count(s) < FULL_MODE_THRESHOLD]

    def get_states_without_recent_file(self):
        return [s for s in ALL_STATES if not os.path.exists(self._csv_path(s, recent=True))]

    def filter_states_with_2000_plus(self, states):
        return [s for s in states if self._existing_lead_count(s) >= FULL_MODE_THRESHOLD]

    # -- API ----------------------------------------------------------------

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _fetch_page(self, state_code, page):
        url = (
            f"{BASE_URL}{SEARCH_ENDPOINT}"
            f"?state={state_code}&page={page}&limit={PAGE_LIMIT}"
        )
        resp = requests.get(url, headers=self._headers(), timeout=60)
        return resp

    # -- Date filtering -----------------------------------------------------

    def _filter_by_date(self, leads):
        if not self.date_from and not self.date_to:
            return leads
        filtered = []
        for lead in leads:
            d = parse_lead_date(lead.get("createdDate"))
            if d is None:
                filtered.append(lead)
                continue
            if self.date_from and d < self.date_from:
                continue
            if self.date_to and d > self.date_to:
                continue
            filtered.append(lead)
        return filtered

    # -- CSV writing --------------------------------------------------------

    def save_leads_to_csv(self, state, leads, recent=False):
        path = self._csv_path(state, recent)
        file_exists = os.path.exists(path) and os.path.getsize(path) > 0
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            for lead in leads:
                row = {}
                for csv_field, api_key in FIELD_MAP.items():
                    row[csv_field] = lead.get(api_key, "")
                writer.writerow(row)
        return path

    # -- Single state scrape ------------------------------------------------

    def scrape_state(self, state_code, recent_mode=False, max_leads=None):
        page = 1
        total = 0
        batch = []
        consecutive_empty = 0

        self.on_log(f"{'─' * 40}", "dim")
        self.on_log(f"▶ Starting {'recent' if recent_mode else 'full'} scrape: {state_code}", "info")

        while not self._stop.is_set():
            if max_leads and total >= max_leads:
                self.on_log(f"  ✓ Hit limit of {max_leads} for {state_code}", "success")
                break

            try:
                resp = self._fetch_page(state_code, page)
            except requests.RequestException as exc:
                retried = self._retry_on_error(state_code, page, str(exc))
                if retried is None:
                    break
                resp = retried

            if resp.status_code == 401:
                self.on_log("⚠ Token expired (401). Attempting re-login…", "warning")
                try:
                    new_token = fetch_token_from_api(DEFAULT_EMAIL, DEFAULT_PASSWORD)
                    if new_token:
                        self.auth_token = new_token
                        save_token(new_token)
                        self.on_log("  Token refreshed. Retrying page…", "success")
                        continue
                except Exception:
                    pass
                self.on_log("  Re-login failed. Stopping.", "error")
                self._stop.set()
                break

            if resp.status_code != 200:
                retried = self._retry_on_error(state_code, page, f"HTTP {resp.status_code}")
                if retried is None:
                    break
                if retried.status_code != 200:
                    self.on_log(f"  ✗ Failed after retries: {state_code} page {page}", "error")
                    break
                resp = retried

            try:
                data = resp.json()
            except ValueError:
                self.on_log(f"  ✗ Invalid JSON on page {page}", "error")
                break

            rows = data.get("leads", {}).get("rows", [])
            leads = [row.get("body", {}) for row in rows if row.get("body")]
            pre_filter = len(leads)
            leads = self._filter_by_date(leads)
            if pre_filter > 0 and not leads:
                self.on_log(f"  Page {page}: {pre_filter} leads filtered out by date range", "dim")

            if not leads:
                consecutive_empty += 1
                if consecutive_empty >= RETRY_COUNT:
                    self.on_log(f"  ✓ No more leads for {state_code} (page {page})", "dim")
                    break
                self.on_log(f"  … Empty page {page}, retry {consecutive_empty}/{RETRY_COUNT}", "warning")
                time.sleep(RETRY_SLEEP)
                continue

            consecutive_empty = 0
            batch.extend(leads)
            total += len(leads)

            if len(batch) >= BATCH_SAVE_SIZE:
                self.save_leads_to_csv(state_code, batch, recent=recent_mode)
                batch = []

            self.on_log(f"  Page {page}: +{len(leads)} leads (total: {total})", "success")
            self.on_progress(state_code, total)

            page += 1
            time.sleep(RATE_LIMIT_SLEEP)

        if batch:
            self.save_leads_to_csv(state_code, batch, recent=recent_mode)

        self.on_state_done(state_code, total)
        return total

    def _retry_on_error(self, state_code, page, error_msg):
        for attempt in range(1, RETRY_COUNT + 1):
            if self._stop.is_set():
                return None
            self.on_log(f"  ⟳ Retry {attempt}/{RETRY_COUNT} ({error_msg})", "warning")
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
        cycle = 0

        while not self._stop.is_set():
            cycle += 1
            self.on_log(f"\n{'═' * 50}", "dim")
            self.on_log(f"  CYCLE {cycle} — {mode.upper()} MODE", "info")
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
                        return
                    time.sleep(1)
                continue

            random.shuffle(work)
            self.on_log(f"  Processing {len(work)} state(s): {', '.join(work)}", "info")

            for state in work:
                if self._stop.is_set():
                    break
                recent = mode == "recent"
                self.scrape_state(state, recent_mode=recent, max_leads=max_leads)

            self.on_cycle_done()

        self.on_log("\n⏹ Scraping stopped.", "warning")

    def stop_scraping(self):
        self._stop.set()


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

        self.scraper = None
        self.scrape_thread = None
        self.auth_token = load_saved_token()
        self.csv_dir = resolve_csv_directory()
        self._token_save_job = None
        self.session_stats = {}
        self.state_vars = {}

        self._setup_ui()
        self._load_token_into_ui()
        if not self.auth_token:
            self.root.after(500, self._auto_login)

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
        tk.Entry(row_from, textvariable=self.date_from_var, font=("Consolas", 10), bg="#45475a", fg="#a6e3a1", insertbackground="#a6e3a1", relief=tk.FLAT, bd=3, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row_to = tk.Frame(date_frame, bg="#313244")
        row_to.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(row_to, text="To:", font=("Helvetica", 9), fg="#cdd6f4", bg="#313244", width=5, anchor=tk.W).pack(side=tk.LEFT)
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y"))
        tk.Entry(row_to, textvariable=self.date_to_var, font=("Consolas", 10), bg="#45475a", fg="#a6e3a1", insertbackground="#a6e3a1", relief=tk.FLAT, bd=3, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            frame, text="Recent limit:", font=("Helvetica", 9),
            fg="#cdd6f4", bg="#313244",
        ).pack(anchor=tk.W, padx=4)

        self.limit_var = tk.StringVar(value="500")
        limit_frame = tk.Frame(frame, bg="#313244")
        limit_frame.pack(fill=tk.X, padx=4, pady=(0, 6))
        for val in ("250", "500", "750", "1500"):
            tk.Radiobutton(
                limit_frame, text=val, variable=self.limit_var, value=val,
                font=("Consolas", 9), fg="#cdd6f4", bg="#313244",
                selectcolor="#45475a", activebackground="#313244",
            ).pack(side=tk.LEFT, padx=2)

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
        """Fetch a fresh token using hardcoded credentials."""
        self._log("Fetching fresh token via login…", "info")
        try:
            token = fetch_token_from_api(DEFAULT_EMAIL, DEFAULT_PASSWORD)
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
            self.log_console.insert(tk.END, f"[{ts}] {message}\n", tag)
            self.log_console.see(tk.END)
            self.log_console.configure(state=tk.DISABLED)

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
        self.btn_stop.configure(state=state_stop)
        self.token_text.configure(state=tk.DISABLED if running else tk.NORMAL)

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

        callbacks = {
            "on_log": self._log,
            "on_progress": self._on_progress,
            "on_state_done": self._on_state_done,
            "on_cycle_done": self._on_cycle_done,
        }
        self.scraper = LeadsScraper(self.auth_token, callbacks, self.csv_dir, date_from=d_from, date_to=d_to)
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

        callbacks = {
            "on_log": self._log,
            "on_progress": self._on_progress,
            "on_state_done": self._on_state_done,
            "on_cycle_done": self._on_cycle_done,
        }
        self.scraper = LeadsScraper(self.auth_token, callbacks, self.csv_dir, date_from=d_from, date_to=d_to)
        self.scrape_thread = threading.Thread(
            target=self._run_scraper, args=(states, "recent", max_leads), daemon=True,
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
        if self.scraper:
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
