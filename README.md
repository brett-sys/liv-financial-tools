# LIV Financial Tools

Internal toolkit for LIV Financial — everything the team needs to sell, track, and manage insurance business.

---

## New to the Team?

Follow the **[Setup Guide](SETUP_GUIDE.md)** to get your machine configured and all tools running.

Deploying to the cloud? See the **[Railway Deployment Guide](DEPLOY_RAILWAY.md)**.

Want to build this toolkit from scratch for a different agency? See the **[Build Prompt Template](GARY_BUILD_PROMPT.md)**.

---

## Tools at a Glance

| Tool | Type | What It Does | How to Run | Port |
|------|------|-------------|------------|------|
| **PDF Generator** | Desktop (Tkinter) | IUL illustrations, policy packets, business cards, quote comparisons, referral tracking | `python -m pdf_generator` | — |
| **Underwriting Tool** | Desktop (Tkinter) | Assess client eligibility across 15 carriers by health factors | `python underwriting/underwriting_tool.py` | — |
| **Agent Toolkit** | Web (Flask) | Unified dashboard: call logging, illustrations, quotes, referrals | `python agent_toolkit/app.py` | 5055 |
| **Call Logger** | Web (Flask) | Standalone call logging with Google Sheets export and calendar integration | `python call_logger/app.py` | 5055 |
| **Lead Manager** | Web (Flask) | Browse leads from Google Drive, import to Go High Level CRM | `python -m lead_manager` | 5070 |
| **Password Vault** | Web (Flask) | Encrypted password manager with PIN auth | `python -m password_vault` | 5050 |
| **Landing Page** | Static HTML | Lead-capture form → Google Sheets | Open `landing/index.html` | — |

> **Agent Toolkit vs Call Logger:** The Agent Toolkit is the newer, all-in-one version that combines call logging with other tools. The standalone Call Logger is the original. Use whichever fits your workflow.

---

## Project Structure

```
python/
├── agent_toolkit/             # Unified web dashboard (Flask)
│   ├── app.py                 #   Main app (port 5055)
│   ├── config.py              #   Agent roster, themes, Google Sheets
│   ├── calls.db               #   Call log database
│   └── referrals.db           #   Referral tracking database
│
├── call_logger/               # Standalone call logger (Flask)
│   ├── app.py                 #   Main app (port 5055)
│   ├── config.py              #   Agent list, Google Sheets config
│   ├── credentials.json       #   Google service account (git-ignored)
│   └── calls.db               #   Call log database
│
├── lead_manager/              # Lead distribution dashboard (Flask)
│   ├── app.py                 #   Main app (port 5070)
│   ├── config.py              #   Google Drive, GHL API config
│   └── agents.json            #   Configurable agent list
│
├── pdf_generator/             # PDF generation GUI (Tkinter)
│   ├── gui.py                 #   Main GUI window
│   ├── config.py              #   ★ Agent info (name, phone, etc.)
│   ├── parsers.py             #   Text parsing logic
│   ├── html_builders.py       #   HTML templates for PDFs
│   ├── pdf_gen.py             #   WeasyPrint rendering
│   ├── referral_tracker.py    #   Referral management
│   ├── ghl_integration.py     #   Go High Level CRM
│   ├── assets/                #   Logos, headshot, business card
│   └── referrals.db           #   Referral database
│
├── underwriting/              # Underwriting risk assessment (Tkinter)
│   ├── underwriting_tool.py   #   Main app
│   ├── underwriting.db        #   Carrier guidelines (15 carriers)
│   └── README.md              #   Carrier details & database schema
│
├── password_vault/            # Encrypted password manager (Flask)
│   ├── app.py                 #   Main app (port 5050)
│   └── vault.db               #   Encrypted storage
│
├── landing/                   # Lead-capture landing page
│   ├── index.html             #   Multi-step form
│   ├── final-expense-questionnaire.html
│   └── form-to-sheet*.gs      #   Google Apps Script handlers
│
├── google_integrations/       # Gmail → Google Sheets automation
│   └── gmail_to_sheets_leadconduit.js
│
├── .env.example               # Environment variable template
├── .env                       # Your API keys (git-ignored)
├── requirements.txt           # Core Python dependencies
├── SETUP_GUIDE.md             # ★ New team member setup
├── DEPLOY_RAILWAY.md          # Cloud deployment guide
└── GARY_BUILD_PROMPT.md       # Build-from-scratch template
```

---

## Tool Details

### PDF Generator

Generates professional insurance PDFs from pasted data.

| Feature | Description |
|---------|-------------|
| **IUL Illustration** | Paste illustration data → multi-page PDF with policy info, cash value graphs, living benefits, NLG overview |
| **Policy Submitted** | Paste confirmation email → formatted confirmation PDF |
| **Business Card** | Generate cards via APITemplate.io API |
| **Quote Comparison** | Enter multiple carrier quotes → side-by-side comparison PDF |
| **Referral Tracker** | SQLite-backed referral management with status tracking and stats |

Personalize it by editing `pdf_generator/config.py` with your name, phone, email, etc. and replacing the headshot in `pdf_generator/assets/`.

### Underwriting Tool

Assess client eligibility across **15 insurance carriers** based on health factors.

- **Product types:** IUL, Term, Final Expense
- **Carriers:** National Life, Transamerica, Mutual of Omaha, Americo, Ethos, InstaBrain, Ladder, Family Freedom, TruStage, Accendo, Royal Neighbors, Living Promise, and more
- **Client factors:** Age, height/weight, BMI (auto-calculated), tobacco, diabetes, hypertension, cancer history, DUI history, 42 medical conditions
- **Output:** Sorted results showing likely approval and rating class per carrier

### Agent Toolkit / Call Logger

Web-based call logging with multi-agent support.

- Per-agent themes and personalized URLs (e.g., `/brett`, `/kevin`)
- Dashboard with call stats, outcome charts, and follow-up reminders
- Google Sheets weekly export (auto-exports Friday at 6 PM)
- Calendar integration (Google Calendar URLs or Outlook .ics files)
- Cloudflare tunnel support for sharing links

### Lead Manager

Browse and distribute leads to agents.

- Reads CSV files from a Google Drive folder
- Import leads to Go High Level CRM with agent tagging
- Manage agent list via the UI

### Password Vault

Secure, encrypted password storage accessible from the browser.

- PIN authentication (PBKDF2 hashed)
- Fernet encryption (AES-128) for all entries
- Categories: Social Media, Insurance Carriers, Tools & Platforms, Email Accounts, Other
- Password generator, copy-to-clipboard, share via email, export to file

### Landing Page

Static HTML lead-capture form that submits to a Google Sheet via Google Apps Script. See `landing/README.md` for deployment.

### Gmail → Sheets Automation

Google Apps Script that scans Gmail for LeadConduit lead emails and writes parsed data to a Google Sheet. Runs on a timer trigger inside Google Apps Script.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. The `.env` file is git-ignored.

| Variable | Used By | Description |
|----------|---------|-------------|
| `APITEMPLATE_API_KEY` | PDF Generator | APITemplate.io key for business cards |
| `GHL_API_KEY` | PDF Generator, Lead Manager | Go High Level CRM API key |
| `GHL_LOCATION_ID` | PDF Generator, Lead Manager | GHL location ID |
| `GHL_WORKFLOW_ID` | PDF Generator | GHL workflow ID |
| `GHL_FILE_CUSTOM_FIELD_ID` | PDF Generator | GHL custom field for file uploads |
| `GHL_ENABLED` | PDF Generator | Enable/disable GHL integration |
| `CALL_LOG_SHEET_ID` | Call Logger, Agent Toolkit | Google Sheet ID for call exports |
| `CALL_LOGGER_SECRET_KEY` | Call Logger, Agent Toolkit | Flask secret key |
| `CALL_LOGGER_PORT` | Call Logger, Agent Toolkit | Server port (default 5055) |
| `VAPID_PRIVATE_KEY` | Agent Toolkit | Web push notification key |
| `VAPID_PUBLIC_KEY` | Agent Toolkit | Web push notification key |
| `LEAD_SHEET_ID` | Lead Manager | Google Sheet ID for leads |
| `LEAD_MANAGER_SECRET_KEY` | Lead Manager | Flask secret key |
| `LEAD_MANAGER_PORT` | Lead Manager | Server port (default 5070) |
| `SMTP_EMAIL` | Lead Manager | Gmail address for sending lead emails |
| `SMTP_PASSWORD` | Lead Manager | Gmail app password |

---

## Quick Start (for Brett / existing setup)

```bash
source venv/bin/activate
pip install -r requirements.txt

# Desktop tools
python -m pdf_generator
python underwriting/underwriting_tool.py

# Web tools
python agent_toolkit/app.py      # http://localhost:5055
python -m password_vault          # http://localhost:5050
python -m lead_manager            # http://localhost:5070
```
