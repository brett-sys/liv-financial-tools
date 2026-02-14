# LIV Financial Tools

Internal tools for LIV Financial: PDF generation for insurance illustrations and an underwriting risk assessment system.

## Project Structure

```
├── pdf_generator/          # IUL Illustration & Policy PDF generator (GUI)
├── underwriting/           # Underwriting risk assessment tool (GUI)
├── landing/                # Lead-capture landing page + Google Sheets integration
├── google_integrations/    # Gmail-to-Sheets lead parsing script
├── scripts/                # Setup & install helper scripts
├── archive/                # Old/test files kept for reference
├── .env.example            # API key template (copy to .env)
└── requirements.txt        # Python dependencies
```

## Quick Start

### 1. Install dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip3 install -r requirements.txt
```

WeasyPrint requires system libraries on macOS. Run the helper script if you haven't already:

```bash
bash scripts/install-weasyprint-deps.sh
```

### 2. Set up your API key

```bash
cp .env.example .env
# Edit .env and paste your APITemplate.io key
```

### 3. Run the apps

**PDF Generator** (IUL illustrations, policy submitted packets, business cards):

```bash
python3 pdf_generator/pdf_generator.py
```

**Underwriting Tool** (carrier eligibility & risk assessment):

```bash
python3 underwriting/underwriting_tool.py
```

---

## PDF Generator

A tkinter GUI app that generates professional insurance PDFs:

- **IUL Illustration** -- Paste illustration data, generates a styled multi-page PDF with policy info, cash value graphs, living benefits summary, and National Life Group overview. Uses WeasyPrint for local PDF generation.
- **Policy Submitted** -- Paste a policy confirmation email to generate a formatted confirmation PDF.
- **Business Card** -- Generate business cards via the APITemplate.io API (requires API key in `.env`).

Logos are stored in `pdf_generator/assets/`.

## Underwriting Tool

A tkinter GUI for assessing client eligibility across multiple insurance carriers:

- Supports **IUL**, **Term**, and **Final Expense** product types
- Pre-loaded with real carrier data: National Life, Transamerica, Mutual of Omaha, Americo, Ethos, and more
- Enter client factors (age, height, weight, tobacco, conditions) and see which carriers approve and at what rating
- Uses a SQLite database (`underwriting/underwriting.db`) for carrier guidelines

See [underwriting/README.md](underwriting/README.md) for full carrier details and how to add your own.

## Landing Page

A multi-step lead-capture form for the burial insurance program. Submissions go to a Google Sheet via Google Apps Script.

See [landing/README.md](landing/README.md) for setup instructions.

## Google Integrations

- `gmail_to_sheets_leadconduit.js` -- Google Apps Script that scans Gmail for LeadConduit lead emails and appends parsed data to a Google Sheet.

---

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `APITEMPLATE_API_KEY` | pdf_generator | APITemplate.io key for business card generation |

Copy `.env.example` to `.env` and fill in your values. The `.env` file is git-ignored.
