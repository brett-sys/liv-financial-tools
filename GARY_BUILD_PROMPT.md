# Insurance Agency Toolkit — Build Prompt

> **Instructions:** Copy this entire prompt into a new Cursor AI Agent chat. Fill in the `[PLACEHOLDER]` fields with your team's info before running. The AI will build your complete toolkit from scratch.

---

## WHO THIS IS FOR

You are building a complete insurance agency toolkit for **[AGENCY_NAME]** (e.g. "LIV Financial Group"). The agency owner is **[OWNER_NAME]** and the team members are listed below. Every tool below should be branded to your agency and customized to your team.

---

## TEAM ROSTER

Fill in your agents. Add or remove as needed:

```
AGENTS:
  - Name: [AGENT_1_NAME]            (e.g. "Gary Smith")
    Email: [AGENT_1_EMAIL]          (e.g. "gary@agency.com")
    Calendar: [google or outlook]
    Phone: [AGENT_1_PHONE]
    License: [AGENT_1_LICENSE]
    Title: [AGENT_1_TITLE]          (e.g. "Licensed Agent")
    Theme Color: [hex color]        (e.g. "#4f8cff" blue)

  - Name: [AGENT_2_NAME]
    Email: [AGENT_2_EMAIL]
    Calendar: [google or outlook]
    Phone: [AGENT_2_PHONE]
    License: [AGENT_2_LICENSE]
    Title: [AGENT_2_TITLE]
    Theme Color: [hex color]        (e.g. "#ff8c00" orange)

  - Name: [AGENT_3_NAME]
    Email: [AGENT_3_EMAIL]
    Calendar: [google or outlook]
    Phone: [AGENT_3_PHONE]
    License: [AGENT_3_LICENSE]
    Title: [AGENT_3_TITLE]
    Theme Color: [hex color]        (e.g. "#34c759" green)
```

---

## TOOL 1: CALL LOGGER (Flask Web App)

Build a Flask call logging web app with the following specs:

### Core Features
- **Dashboard** showing today's calls, this week's calls, outcome breakdown bar chart, and upcoming follow-ups
- **Log Call form** with fields: Agent Name (dropdown), Contact Name (with auto-suggest from past contacts), Phone Number, Date/Time, Direction (Inbound/Outbound toggle), Outcome (toggle buttons), Notes (textarea), Follow-up Date (optional)
- **Call History** page with filters: agent, direction, outcome, free-text search, date range
- **Edit/Delete** existing call records
- **Contact auto-suggest** API endpoint that returns previous contacts matching a partial query

### Multi-Agent Theme System
Each agent gets their own personalized URL shortcut (e.g. `/gary`, `/mike`, `/sarah`) that:
- Sets a cookie with `theme=[agent_slug]` and `agent_pref=[Agent Full Name]` (1 year expiry)
- Redirects to the dashboard
- The base HTML template applies `class="theme-{{ theme }}"` to `<body>`
- Each theme has its own CSS color scheme (dark background + agent's accent color for primary, buttons, badges, links)
- Default theme detection: if no cookie, localhost = first agent's theme, otherwise = second agent's theme

### Theme CSS Structure
The default theme (first agent) is defined in CSS `:root` variables:
```
--bg: #0f1117;           (dark background)
--surface: #1a1d27;      (card/panel background)
--surface-hover: #22262f;
--border: #2a2e3a;
--text: #e4e6eb;
--text-muted: #8b8fa3;
--primary: [AGENT_COLOR]; (accent color)
--primary-hover: [darker shade];
--success: #34c759;
--danger: #ff453a;
--warning: #ff9f0a;
```
Each additional agent gets a `.theme-[slug]` class that overrides these variables with their color.

### Config Structure
```python
DIRECTION_CHOICES = ["Inbound", "Outbound"]
OUTCOME_CHOICES = ["Sale", "Callback", "No Answer", "Voicemail", "Not Interested", "Other"]
AGENT_CHOICES = ["Agent 1 Name", "Agent 2 Name", ...]
AGENT_EMAILS = {"Agent 1 Name": "email@...", ...}
CALENDAR_REMINDER_MINUTES = 30
```

### Database (SQLite)
```sql
CREATE TABLE calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL DEFAULT '',
    contact_name TEXT NOT NULL DEFAULT '',
    phone_number TEXT NOT NULL DEFAULT '',
    call_datetime TEXT NOT NULL,
    direction TEXT NOT NULL,
    outcome TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    follow_up_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

### Google Sheets Export
- Uses `gspread` + Google service account credentials
- **Per-agent tabs**: each agent gets their own tab named `"{Agent Name} - {Week Label}"` (e.g. "Gary - Feb 17-21, 2026")
- Each tab has: header row, that agent's calls only, summary section with total calls and outcome breakdown
- Bold header row formatting
- Manual export button on dashboard + automatic scheduled export

### Scheduled Export
- Uses APScheduler `BackgroundScheduler`
- Runs every Friday at 6:00 PM
- Calls the same export function as the manual button

### Calendar Integration
- When a follow-up date is set on a call, auto-generate a calendar event
- **Google Calendar agents**: generate a Google Calendar URL that opens in a new tab with event pre-filled (30-minute event at 9 AM on the follow-up date, with contact name + phone in title and notes in description)
- **Outlook agents**: generate and auto-download an `.ics` file (RFC 5545 VCALENDAR format)
- Detection: check `AGENT_EMAILS` — if email contains "outlook", use .ics; otherwise use Google Calendar URL

### Cloudflare Tunnel + Link Sharing
Create a `start.sh` bash script that:
1. Kills any existing Flask server on the port and any existing `cloudflared tunnel` processes
2. Starts the Flask server in background (logging to `app.log`)
3. Waits for server to be ready (curl health check loop)
4. Starts `cloudflared tunnel --url http://localhost:[PORT]`
5. Parses stdout for the `trycloudflare.com` URL
6. Prints each agent's personalized link: `{URL}/[agent_slug]`
7. Uses inline Python to update a Google Sheet with each agent's link tab (one tab per remote agent, formatted with bold header and blue link text)

### UI/UX Details
- Dark theme, modern, mobile-responsive
- Navbar with logo image, brand name link, and nav links (Dashboard, Log Call, History)
- Flash messages for success/error feedback
- Toggle button groups for Direction and Outcome (not dropdowns)
- Sticky navbar
- Cards with subtle borders and rounded corners
- Outcome bar chart on dashboard with color-coded bars (green=Sale, blue=Callback, orange=No Answer, purple=Voicemail, red=Not Interested, gray=Other)
- Port: 5055

---

## TOOL 2: UNDERWRITING RISK ASSESSMENT (Tkinter Desktop App)

Build a Tkinter GUI application for assessing client eligibility across multiple insurance carriers.

### Product Types
- **IUL** (Indexed Universal Life)
- **Term** (Term Life Insurance)
- **Final Expense** (Burial/Funeral Insurance)

### Carriers Database (SQLite)

Store all carrier data in an SQLite database (`underwriting.db`) with these tables:

**Table `carriers`:**
```sql
CREATE TABLE carriers (
    id INTEGER PRIMARY KEY,
    name TEXT, product_type TEXT,
    bmi_min REAL, bmi_max_standard REAL,
    bmi_max_table2 REAL, bmi_max_table4 REAL,
    bmi_max_table6 REAL, bmi_max_table8 REAL,
    min_age INTEGER, max_age INTEGER,
    tobacco_standard INTEGER, tobacco_table2 INTEGER, tobacco_decline INTEGER,
    diabetes_ok INTEGER, hypertension_ok INTEGER,
    cancer_history_years INTEGER,
    dui_years_standard INTEGER, dui_years_table INTEGER,
    notes TEXT, guaranteed_issue INTEGER DEFAULT 0
);
```
- `diabetes_ok` / `hypertension_ok`: 0=decline, 1=table rating, 2=standard OK
- `tobacco_standard`: 1=tobacco users can get Standard, 0=no
- `tobacco_table2`: 1=tobacco users get Table 2, 0=no
- `cancer_history_years`: minimum years cancer-free required

**Table `carrier_build`** (height/weight charts for carriers that use them):
```sql
CREATE TABLE carrier_build (
    id INTEGER PRIMARY KEY, carrier_id INTEGER,
    height_inches INTEGER,
    w_standard INTEGER, w_table2 INTEGER, w_table4 INTEGER,
    w_table6 INTEGER, w_table8 INTEGER, w_table10 INTEGER,
    FOREIGN KEY (carrier_id) REFERENCES carriers(id)
);
```

**Table `conditions`** (42 medical conditions):
```sql
CREATE TABLE conditions (
    id INTEGER PRIMARY KEY, code TEXT UNIQUE,
    name TEXT, category TEXT  -- 'knockout' or 'declinable'
);
```

**Table `carrier_conditions`** (how each carrier handles each condition):
```sql
CREATE TABLE carrier_conditions (
    carrier_id INTEGER, condition_code TEXT,
    action TEXT,  -- 'decline', 'table', or 'ok'
    PRIMARY KEY (carrier_id, condition_code)
);
```

### Carrier Data to Populate

**IUL Carriers (5):**

1. **National Life** — Age 18-85, BMI Standard ≤29.9 / T2 ≤32.7 / T4 ≤37.5 / T6 ≤42.5 / T8 ≤46.5, Tobacco Standard+T2, Diabetes Decline, Hypertension OK if controlled, Cancer 3-5yr, DUI 5yr table/10yr standard. Has height/weight build chart. Rating tiers: Elite/Preferred/Select/Express Std1/Express Std2/Table 8.

2. **Transamerica FFIUL** — Age 18-85, BMI Std ≤28.2 / T2 ≤31.0 / T4 ≤33.4 / T6 ≤36.0 / T8 ≤40.0, Tobacco Standard+T2, Diabetes OK, Hypertension OK, Cancer 10yr, DUI 10yr std/5yr table.

3. **Mutual of Omaha IUL Express** — Age 18-75, BMI Std ≤42.0, Tobacco T2 only, Diabetes Decline, Hypertension OK, Cancer 10yr, DUI 5yr. Simplified issue $25K-$300K.

4. **Americo Instant Decision IUL** — Age 18-65, BMI Std ≤42.0, Tobacco T2 only (non-nicotine 24mo), Diabetes Decline, Hypertension OK, Cancer 10yr, DUI 10yr std/5yr table. No substandard.

5. **Ethos (Ameritas) IUL** — Age 18-70, BMI Std ≤49.0 / T2 ≤41.5, Tobacco T2 only, Diabetes OK if 35+ w/ A1C ≤9.5, Hypertension OK, Cancer 10yr, DUI 5yr.

**Term Carriers (5):**

6. **Ethos Term** — Age 18-60, BMI Std ≤30.0 / T2 ≤32.0 / T4 ≤37.0 / T6 ≤42.0 / T8 ≤46.5, Tobacco Standard+T2, Diabetes OK (table), Hypertension OK, Cancer 10yr, DUI 10yr std/5yr table.

7. **InstaBrain (Fidelity Life) Term** — Age 18-60, BMI Pref+ ≤28.0 / Pref ≤30.0 / Std ≤32.0 / StdExtra ≤37.0, Tobacco T2 only, Diabetes Decline, Hypertension OK, Cancer 10yr, DUI 5yr. Has build chart.

8. **Ladder Term** — Age 20-60, BMI Pref+ ≤28.0 / Pref ≤30.0 / Std+ ≤32.0 / Std ≤37.0, Tobacco T2 only, Diabetes OK (Type 2 controlled), Hypertension OK, Cancer 10yr, DUI 10yr std/5yr table.

9. **Family Freedom (Transamerica) Term** — Age 18-75, BMI Std ≤40.0 / T2 ≤42.0 / T4 ≤45.0, Tobacco T2 only, Diabetes OK, Hypertension OK, Cancer 5yr, DUI 5yr std/3yr table. $50K-$500K simplified.

10. **TruStage Term** — Age 18-70, BMI Std ≤35.0 / T2 ≤38.0 / T4 ≤40.0, Tobacco T2 only, Diabetes Decline, Hypertension OK, Cancer 10yr, DUI 10yr std/5yr table.

**Final Expense Carriers (5):**

11. **Accendo (Aetna/CVS)** — Age 40-89, BMI Std ≤50.0 / T2 ≤52.0 / T4 ≤55.0, Tobacco T2, Diabetes OK, Hypertension OK, Cancer 2yr, DUI 5yr std/2yr table. $2K-$50K.

12. **Americo Eagle Select** — Age 40-85, BMI Std ≤45.0 / T2 ≤48.0 / T4 ≤52.0, Tobacco T2, Diabetes OK, Hypertension OK, Cancer 5yr, DUI 5yr std/3yr table. Up to $40K.

13. **Fidelity Life RAPIDecision GI** — Age 50-85, BMI ≤60.0 all tiers, Tobacco T2, Diabetes OK, Hypertension OK, Cancer no restriction, Guaranteed Issue. $5K-$25K graded benefit.

14. **Royal Neighbors Ensured Legacy** — Age 18-85, BMI Std ≤42.0 / T2 ≤45.0 / T4 ≤48.0, Tobacco T2, Diabetes OK (no insulin), Hypertension OK, Cancer 5yr, DUI 5yr std/3yr table.

15. **Living Promise** — Age 18-85, BMI Std ≤44.0 / T2 ≤47.0 / T4 ≤50.0, Tobacco T2, Diabetes OK, Hypertension OK, Cancer 4yr, DUI 5yr std/2yr table.

### Medical Conditions (42 total)

**Knockouts (10):** HIV/AIDS, Organ/bone marrow transplant, ALS/MS/Parkinson's, Current dialysis/renal failure, Drug/substance abuse (current), Prior life insurance decline, Metastatic/recurrent cancer, Mental incapacity, Paralysis, Sickle cell anemia.

**Declinable (32):** Abnormal heart rhythm, Alcohol/drug treatment history, Amputation (disease-caused), Asthma (chronic/severe), Bipolar/schizophrenia/major depression, Cardiomyopathy, Cerebral palsy, Chronic kidney disease, CHF, Crohn's/ulcerative colitis, Coronary disease/heart attack/surgery, COPD/bronchitis/emphysema/cystic fibrosis, Cancer history, Defibrillator, Diabetes with complications, Heart disease/surgery, Hepatitis B/C, Hodgkin's disease, Liver disease/cirrhosis, Leukemia, Lymphoma, Melanoma, Muscular dystrophy/neurological disorders, Pacemaker, Pancreatitis (chronic/alcohol), PVD/PAD, Renal insufficiency, Rheumatoid arthritis (moderate/severe), Scleroderma, Stroke/TIA, Seizure disorder, Sleep apnea (untreated/severe).

### Assessment Logic
1. Check age against carrier min/max → Decline if outside range
2. Check BMI/build: use carrier build chart if available (height+weight), otherwise use BMI limits → determine rating tier or Decline
3. Check tobacco → Standard, Table, or Decline per carrier rules
4. Check diabetes → Standard OK, Table, or Decline per carrier
5. Check hypertension → same logic
6. Check cancer history years → Decline if too recent
7. Check DUI years → Decline, Table, or Standard per carrier thresholds
8. Check selected medical conditions against carrier_conditions table → decline, table, or ok
9. **Worst factor wins** — final rating is the worst (highest table number) across all checks

### GUI Layout (Tkinter)
- 780x780 window
- Header with agency logo + title "Underwriting Risk Assessment"
- Product type dropdown (IUL/Term/Final Expense) — filters carriers
- Client factors panel: Age, Height (inches), Weight (lbs), BMI (auto-calculated), Tobacco checkbox, Diabetes checkbox, Hypertension checkbox, Cancer years ago, DUI years ago
- Scrollable conditions panel with checkboxes in 2-column grid
- "Assess" button
- Results treeview table: Carrier | Likely Rating | Notes
- Color-coded rows: green=Standard/Preferred, orange=Table ratings, red=Decline, gray=Graded/GI
- Results sorted: approved carriers first (best rating at top), then declined

---

## TOOL 3: PDF GENERATOR (Tkinter Desktop App)

Build a Tkinter GUI for generating professional insurance PDFs.

### Features
1. **IUL Illustration PDF** — Paste illustration data → multi-page PDF with:
   - Header with agency logo + agent info (name, title, phone, email, license, website, headshot)
   - Client name + date stamp
   - Policy values table parsed from pasted data
   - Initial Policy Information cards
   - Cash Value vs Premiums Paid bar chart (HTML/CSS based)
   - "Understanding Your Illustration" narrative section
   - Living Benefits summary page
   - Footer on every page

2. **Policy Submitted Packet** — Paste confirmation email → formatted PDF with policy details

3. **Business Card PDF** — Generate from a business card image using APITemplate.io API or local image

4. **Quote Comparison** — Dialog to enter multiple carrier quotes → side-by-side comparison PDF with "Recommended" badge on best option

5. **Referral Tracker** — Separate window with SQLite-backed referral management:
   - Add referrals (referrer name, referred person, contact info, notes)
   - Track status: New → Contacted → Quoted → Applied → Sold → Lost
   - Update status with optional premium amount
   - Delete referrals
   - Stats: total, sold, conversion rate, top referrers

### Tech Stack
- Tkinter GUI (900x700 window)
- WeasyPrint for HTML → PDF conversion
- SQLite for referral tracking
- APITemplate.io for business cards (optional)
- Go High Level CRM integration (optional): upsert contact, upload PDF, trigger workflow

### Config
```python
AGENT_NAME = "[AGENT_NAME]"
AGENT_TITLE = "[AGENT_TITLE]"
AGENT_PHONE = "[AGENT_PHONE]"
AGENT_EMAIL = "[AGENT_EMAIL]"
AGENT_LICENSE = "[AGENT_LICENSE]"
AGENT_WEBSITE = "[AGENT_WEBSITE]"
```
Agent headshot: `assets/agent_headshot.png`
Business card: `assets/business_card.png`
Agency logo: `assets/[logo_file]`

---

## TOOL 4: PASSWORD VAULT (Flask Web App)

Build a Flask web app for encrypted password management.

### Features
- PIN authentication (4+ digits, PBKDF2 hashed with 200K iterations)
- Fernet encryption (AES-128) for all stored credentials
- Categories: Social Media, Insurance Carriers, Tools & Platforms, Email Accounts, Other
- CRUD for password entries (title, username, password, URL, notes, category)
- Copy to clipboard, share via email (mailto link), export as .txt file
- Password generator
- Change PIN (re-encrypts all entries with new key)
- Dark theme with purple accents
- Auto-opens browser on launch
- Port: 5050

### Database
```sql
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, title TEXT NOT NULL,
    username TEXT NOT NULL, password TEXT NOT NULL,
    url TEXT DEFAULT '', notes TEXT DEFAULT '',
    created TEXT NOT NULL, updated TEXT NOT NULL
);
```

---

## TOOL 5: LEAD CAPTURE LANDING PAGE (Static HTML + Google Apps Script)

Build a responsive landing page for lead capture.

### Design
- Multi-step form (2 steps with smooth transition)
- Step 1: Full Name, Phone, Email, City, State, Date of Birth
- Step 2: Beneficiary (radio), Financial Goal (radio), Desired Monthly Payment (radio)
- Agency branding, cream/gold color scheme
- Mobile-responsive
- Form validation with error highlighting

### Backend
- Google Apps Script (`form-to-sheet.gs`) that receives POST data
- Writes to a Google Sheet with columns matching form fields
- Returns a thank-you HTML page
- Auto-creates header row if sheet is empty

---

## TOOL 6: GMAIL → GOOGLE SHEETS AUTOMATION (Google Apps Script)

Build a Google Apps Script that:
- Runs every 5 minutes via time-based trigger
- Searches Gmail for unread emails from a specific sender (lead provider)
- Parses structured email content to extract lead fields
- Writes parsed data to a Google Sheet
- Marks processed emails as read
- Handles duplicate detection

---

## TOOL 7: LEAD DISTRIBUTION DASHBOARD (Flask Web App)

Build a Flask web app for managing, assigning, and distributing leads to agents via a Google Sheet backend.

### How It Works
- Leads live in a master Google Sheet (one worksheet) with columns A–M
- The Flask dashboard reads/writes to that sheet via `gspread`
- Managers assign leads to agents from the dashboard, which updates the sheet and emails the agent
- Uses the same `credentials.json` service account as the Call Logger

### Google Sheet Structure (columns A–M)
```
A: Date Added       — timestamp
B: Name             — lead full name
C: Phone            — phone number
D: Email            — lead email
E: State            — state
F: DOB / Age        — date of birth or age
G: Lead Type        — FE, IUL, Term, etc.
H: Source           — where the lead came from (manual, landing page, vendor, etc.)
I: Details          — any extra info (goal, monthly savings, beneficiary, etc.)
J: Assigned To      — agent name (blank = unassigned)
K: Status           — New / Sent / Contacted / Sold / Dead
L: Sent Date        — when the lead was emailed to the agent
M: Notes            — manager notes
```

### Pages

1. **Lead Queue** (`/`) — main view
   - Table of all leads from the sheet
   - Filter by: status, lead type, assigned agent, unassigned only
   - Search by name/phone
   - Bulk select checkboxes
   - Assign dropdown + "Send" button per lead (unassigned leads)
   - Status update dropdown per lead (assigned leads)
   - Bulk assign: select multiple leads, pick agent, send all at once
   - Detail sub-rows showing extra info and notes

2. **Agent Config** (`/agents`) — manage agents
   - Add/remove agents (name + email)
   - Stored in a local JSON config file (`agents.json`)
   - No hardcoded agent list

3. **Stats** (`/stats`) — simple overview
   - Summary cards: total leads, unassigned count, sent today, sold count
   - Leads by status (horizontal bar chart, color-coded)
   - Leads per agent (horizontal bar chart)
   - Leads by type (horizontal bar chart)

### Email Format

When you click "Send", the dashboard:
1. Updates the Google Sheet row: sets Assigned To, Status = "Sent", Sent Date = now
2. Sends an email to the agent with the lead details:
   - Subject: `"New Lead: [Name] - [Lead Type] - [State]"`
   - Body: all lead fields in a clean plaintext format
   - Uses `smtplib` with Gmail SMTP (TLS on port 587) and an App Password from `.env`

### Config Structure
```python
GOOGLE_SHEETS_CREDENTIALS = PROJECT_ROOT / "call_logger" / "credentials.json"
LEAD_SHEET_ID = os.getenv("LEAD_SHEET_ID", "")
LEAD_WORKSHEET_NAME = os.getenv("LEAD_WORKSHEET_NAME", "Leads")
SECRET_KEY = os.getenv("LEAD_MANAGER_SECRET_KEY", "lead-mgr-dev-key-change-me")
PORT = int(os.getenv("LEAD_MANAGER_PORT", "5060"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
STATUS_CHOICES = ["New", "Sent", "Contacted", "Sold", "Dead"]
LEAD_TYPE_CHOICES = ["FE", "IUL", "Term", "Other"]
```

### Sheet Column Mapping (0-indexed)
```python
COL = {
    "date_added": 0, "name": 1, "phone": 2, "email": 3,
    "state": 4, "dob_age": 5, "lead_type": 6, "source": 7,
    "details": 8, "assigned_to": 9, "status": 10,
    "sent_date": 11, "notes": 12,
}
```

### Tech Stack
- Flask on port 5060
- `gspread` for Google Sheets read/write (reuses existing `credentials.json`)
- `smtplib` for email (Gmail SMTP with App Password)
- Dark theme UI matching the Call Logger style (same CSS variables and color scheme)
- Agent config in `lead_manager/agents.json`

### UI/UX Details
- Dark theme with same CSS variables as Call Logger (`--bg: #0f1117`, `--surface: #1a1d27`, `--primary: #4f8cff`, etc.)
- Sticky navbar with brand + nav links (Queue, Stats, Agents)
- Flash messages for success/error feedback
- Filter bar with search, dropdowns, and unassigned checkbox
- Responsive design (mobile-friendly grid breakpoints)
- Color-coded status badges (blue=New, orange=Sent, purple=Contacted, green=Sold, gray=Dead)
- Horizontal stat bar charts with matching status colors
- Port: 5060

---

## PROJECT STRUCTURE

```
[project_root]/
├── call_logger/
│   ├── app.py                 # Flask app
│   ├── config.py              # Configuration
│   ├── models.py              # SQLite models
│   ├── sheets.py              # Google Sheets export
│   ├── calendar_integration.py # Calendar events
│   ├── scheduler.py           # APScheduler
│   ├── start.sh               # Startup script
│   ├── credentials.json       # Google service account
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html         # Dashboard
│   │   ├── log.html           # Log call form
│   │   ├── edit.html          # Edit call
│   │   ├── history.html       # Call history
│   │   └── cal_redirect.html  # Calendar redirect
│   └── static/
│       └── style.css
│
├── underwriting/
│   ├── underwriting_tool.py   # Tkinter app
│   ├── underwriting.db        # Carrier database
│   └── assets/
│       └── [agency_logo]
│
├── pdf_generator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── gui.py                 # Tkinter GUI
│   ├── config.py              # Agent info + API keys
│   ├── parsers.py             # Text parsing
│   ├── html_builders.py       # HTML templates
│   ├── pdf_gen.py             # WeasyPrint rendering
│   ├── assets.py              # Base64 image loading
│   ├── referral_tracker.py    # Referral management
│   ├── ghl_integration.py     # Go High Level CRM
│   └── assets/
│       ├── agent_headshot.png
│       ├── business_card.png
│       └── [agency_logo]
│
├── password_vault/
│   ├── __main__.py
│   ├── app.py                 # Flask app
│   └── templates/
│       ├── login.html
│       └── vault.html
│
├── lead_manager/
│   ├── app.py                 # Flask app (routes, email sending)
│   ├── config.py              # Config (sheet ID, SMTP, port)
│   ├── sheets.py              # Google Sheets read/write helpers
│   ├── agents.json            # Configurable agent list
│   ├── templates/
│   │   ├── base.html          # Base template (dark theme, navbar)
│   │   ├── queue.html         # Lead queue with filters + assign/send
│   │   ├── agents.html        # Agent management page
│   │   └── stats.html         # Stats overview
│   └── static/
│       └── style.css          # Dark theme CSS
│
├── landing/
│   ├── index.html             # Lead capture form
│   └── form-to-sheet.gs       # Google Apps Script
│
├── google_integrations/
│   └── gmail_to_sheets.js     # Gmail parser script
│
├── requirements.txt
├── .env.example
└── .env
```

## DEPENDENCIES (requirements.txt)

```
requests
Pillow
weasyprint
python-dotenv
flask
cryptography
gspread
google-auth
google-api-python-client
APScheduler
```

## ENVIRONMENT VARIABLES (.env.example)

```
# APITemplate.io (business cards)
APITEMPLATE_API_KEY=

# Go High Level CRM (optional)
GHL_API_KEY=
GHL_LOCATION_ID=
GHL_WORKFLOW_ID=
GHL_FILE_CUSTOM_FIELD_ID=
GHL_ENABLED=false

# Call Logger
CALL_LOG_SHEET_ID=
CALL_LOGGER_SECRET_KEY=change-me
CALL_LOGGER_PORT=5055

# Lead Distribution Dashboard
LEAD_SHEET_ID=
LEAD_MANAGER_SECRET_KEY=change-me
LEAD_MANAGER_PORT=5060

# SMTP (Gmail) — used by Lead Manager
SMTP_EMAIL=
SMTP_PASSWORD=
```

---

## BUILD INSTRUCTIONS

Build all 7 tools with the team roster and configuration above. Use the exact database schemas, feature specs, and project structure described. Make sure:

1. All tools run independently
2. The call logger supports all agents with their own themes and tunnel links
3. The underwriting tool has all 15 carriers with correct guidelines pre-populated in the database
4. The PDF generator uses the first agent's info by default (configurable in config.py)
5. The lead manager reuses the call logger's `credentials.json` for Google Sheets access
6. All UI is dark-themed, modern, and mobile-responsive where applicable
7. Include a `venv` setup in instructions and a clear README

Start building now. Create each tool one at a time, starting with the call logger.
