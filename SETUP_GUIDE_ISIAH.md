# LIV Financial Tools — Setup Guide for Isiah

> **Platform:** Windows PC
> **Prepared by:** Brett Dunham
> **Last updated:** February 2026

Welcome to the team toolkit. This guide walks you through setting up **Cursor IDE** and all the LIV Financial tools on your Windows machine so you have the same development environment Brett uses.

---

## Table of Contents

1. [Install Cursor IDE](#1-install-cursor-ide)
2. [Install Python](#2-install-python)
3. [Install Git](#3-install-git)
4. [Clone the Repository](#4-clone-the-repository)
5. [Set Up the Python Environment](#5-set-up-the-python-environment)
6. [Install System Dependencies (WeasyPrint)](#6-install-system-dependencies-weasyprint)
7. [Configure Environment Variables](#7-configure-environment-variables)
8. [Personalize Agent Info](#8-personalize-agent-info)
9. [Configure Cursor Settings](#9-configure-cursor-settings)
10. [Run the Tools](#10-run-the-tools)
11. [Tool Reference](#11-tool-reference)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Install Cursor IDE

Cursor is a VS Code-based editor with built-in AI capabilities.

1. Go to [https://cursor.com](https://cursor.com)
2. Download the **Windows** installer
3. Run the installer and follow the prompts
4. Open Cursor once installation completes
5. Sign in or create a Cursor account when prompted

### Recommended Cursor Settings

After installation, open the Command Palette (`Ctrl+Shift+P`) and type **"Preferences: Open User Settings (JSON)"**. Add these settings:

```json
{
    "window.commandCenter": true,
    "cursor.composer.shouldChimeAfterChatFinishes": true,
    "workbench.editor.enablePreview": false
}
```

| Setting | What It Does |
|---------|--------------|
| `window.commandCenter` | Shows the command center in the title bar for quick access |
| `cursor.composer.shouldChimeAfterChatFinishes` | Plays a sound when the AI finishes a response |
| `workbench.editor.enablePreview` | Prevents files from opening in preview mode (single-click opens permanently) |

> **Settings file location on Windows:**
> `%APPDATA%\Cursor\User\settings.json`

---

## 2. Install Python

The tools require **Python 3.10 or newer**.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest Python 3.x installer for Windows
3. **IMPORTANT:** During installation, check the box that says **"Add Python to PATH"**
4. Click "Install Now"

Verify it worked — open a terminal in Cursor (`` Ctrl+` ``) and run:

```powershell
python --version
```

You should see something like `Python 3.12.x` or newer.

---

## 3. Install Git

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and run the installer
3. Use the default options (just click Next through the wizard)

Verify:

```powershell
git --version
```

---

## 4. Clone the Repository

Open a terminal in Cursor and run:

```powershell
cd C:\Users\Isiah\Desktop
git clone <REPO_URL_HERE> python
cd python
```

> **Note:** Ask Brett for the repository URL. If the repo is private, you'll need to set up GitHub authentication first. Brett can add you as a collaborator.

---

## 5. Set Up the Python Environment

From the project root (`C:\Users\Isiah\Desktop\python`):

```powershell
# Create a virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install Password Vault dependencies
pip install -r password_vault\requirements.txt
```

> **Every time** you open a new terminal to work on these tools, activate the virtual environment first:
> ```powershell
> venv\Scripts\activate
> ```

---

## 6. Install System Dependencies (WeasyPrint)

The PDF Generator uses **WeasyPrint**, which requires GTK libraries on Windows.

### Option A: Install via MSYS2 (Recommended)

1. Download MSYS2 from [https://www.msys2.org/](https://www.msys2.org/)
2. Run the installer, use the default install path (`C:\msys64`)
3. Open the **MSYS2 MINGW64** terminal and run:

```bash
pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-cairo mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-libffi
```

4. Add `C:\msys64\mingw64\bin` to your Windows **PATH** environment variable:
   - Press `Win+R`, type `sysdm.cpl`, press Enter
   - Go to **Advanced** tab → **Environment Variables**
   - Under **System variables**, find `Path`, click **Edit**
   - Click **New** and add: `C:\msys64\mingw64\bin`
   - Click **OK** on all dialogs
   - **Restart Cursor** for the change to take effect

### Option B: Install via GTK Installer

1. Go to the [WeasyPrint Windows docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)
2. Follow the instructions for installing GTK3 on Windows

### Verify WeasyPrint Works

```powershell
venv\Scripts\activate
python -c "import weasyprint; print('WeasyPrint OK')"
```

If you see `WeasyPrint OK` with no errors, you're good.

---

## 7. Configure Environment Variables

The Business Card feature in the PDF Generator uses the APITemplate.io API.

```powershell
copy .env.example .env
```

Then open `.env` in Cursor and replace the placeholder with your real API key:

```
APITEMPLATE_API_KEY=your_actual_api_key_here
```

> Get an API key at [https://apitemplate.io](https://apitemplate.io), or ask Brett if you should use a shared key.

---

## 8. Personalize Agent Info

The PDF Generator embeds agent info (name, phone, email, etc.) into every PDF it creates. You need to update this with **your** details.

Open `pdf_generator/config.py` and update these lines:

```python
# Agent info (shown in PDF header) — update these with your real details
AGENT_NAME = "Isiah [Your Last Name]"
AGENT_TITLE = "Licensed Agent"
AGENT_PHONE = "(XXX) XXX-XXXX"
AGENT_EMAIL = "isiah@fflliv.com"
AGENT_LICENSE = "License #XXXXXXXX"
AGENT_WEBSITE = "www.livfinancialgroup.com"
```

You'll also want to replace the headshot image:
- Replace `pdf_generator/assets/agent_headshot.png` with your own professional headshot
- Keep the filename the same, or update `AGENT_PHOTO_FILENAME` in `config.py`

And if you have your own business card design:
- Replace `pdf_generator/assets/business_card.png`

---

## 9. Configure Cursor Settings

### 9a. Cursor AI Model & Chat

When you open the AI chat panel (sidebar or `Ctrl+L`):
- You can choose which AI model to use in the dropdown
- Brett uses the most capable model available for complex tasks
- The "Agent" mode gives the AI access to tools like running code, reading/writing files, and searching

### 9b. Extensions (Optional but Recommended)

Open Extensions (`Ctrl+Shift+X`) and install:

| Extension | Purpose |
|-----------|---------|
| **Python** (Microsoft) | Python language support, IntelliSense, debugging |
| **Pylance** (Microsoft) | Fast Python type checking and auto-complete |
| **SQLite Viewer** | View `.db` database files directly in the editor |
| **GitLens** | Enhanced Git history and blame annotations |

---

## 10. Run the Tools

Make sure your virtual environment is activated first:

```powershell
venv\Scripts\activate
```

### PDF Generator

Generates professional insurance PDFs — IUL illustrations, policy submitted packets, business cards, and quote comparisons.

```powershell
python -m pdf_generator
```

Or:

```powershell
python pdf_generator\pdf_generator.py
```

### Underwriting Tool

Assesses client eligibility across multiple insurance carriers based on health factors.

```powershell
python underwriting\underwriting_tool.py
```

### Password Vault

A secure web-based password manager (runs in your browser).

```powershell
python -m password_vault
```

Then open [http://localhost:5050](http://localhost:5050) in your browser.

> On first launch, you'll be prompted to create a PIN.

---

## 11. Tool Reference

### PDF Generator Features

| Feature | Description |
|---------|-------------|
| **IUL Illustration** | Paste illustration data → multi-page PDF with policy info, cash value graphs, living benefits summary, NLG overview |
| **Policy Submitted** | Paste confirmation email → formatted confirmation PDF |
| **Business Card** | Generate business cards via APITemplate.io API |
| **Quote Comparison** | Compare multiple carrier quotes side-by-side |
| **Referral Tracker** | SQLite-backed referral management system |

### Underwriting Tool Features

| Feature | Description |
|---------|-------------|
| **Product Types** | IUL, Term, Final Expense |
| **Carriers** | National Life, Transamerica, Mutual of Omaha, Americo, Ethos, InstaBrain, Ladder, Family Freedom, TruStage, Accendo, Royal Neighbors, Living Promise |
| **Client Factors** | Age, height, weight, BMI (auto-calculated), tobacco, diabetes, hypertension, cancer history, DUI history, medical conditions |
| **Results** | Sorted by best rating, shows likely approval and rating class |

### Password Vault Features

| Feature | Description |
|---------|-------------|
| **PIN Authentication** | PBKDF2-based secure PIN |
| **Encrypted Storage** | Fernet encryption for all passwords |
| **Categories** | Social Media, Insurance Carriers, Tools & Platforms, Email Accounts, Other |
| **Sharing** | Share entries via email (mailto: link) |
| **Export** | Export to text file |

### Landing Page

A lead-capture form for the burial insurance program located in the `landing/` directory. Submissions route to a Google Sheet via Google Apps Script. See `landing/README.md` for details.

### Google Integrations

`google_integrations/gmail_to_sheets_leadconduit.js` — A Google Apps Script that scans Gmail for LeadConduit lead emails and appends parsed data to a Google Sheet.

---

## 12. Troubleshooting

### "python is not recognized"
- Make sure you checked **"Add Python to PATH"** during installation
- Try `py` instead of `python`
- Restart your terminal or Cursor

### WeasyPrint errors about missing libraries
- Make sure `C:\msys64\mingw64\bin` is in your system PATH
- Restart Cursor after changing PATH
- Try reinstalling: `pip install --force-reinstall weasyprint`

### "ModuleNotFoundError: No module named ..."
- Make sure your virtual environment is activated: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Database errors
- The `.db` files are SQLite databases. If one gets corrupted, you can pull a fresh copy from the repo with:
  ```powershell
  git checkout -- underwriting/underwriting.db
  ```

### tkinter not found
- tkinter ships with the standard Python installer on Windows. If it's missing, reinstall Python and make sure to check **"tcl/tk and IDLE"** in the optional features.

### Cursor loads but buttons don't work / UI is frozen

This is a known issue on some Windows machines, usually caused by GPU rendering problems.

**Try these fixes in order:**

1. **Run as Administrator**
   - Right-click the Cursor shortcut → **Run as administrator**

2. **Disable GPU acceleration** (most common fix)
   - Close Cursor completely (check Task Manager with `Ctrl+Shift+Esc` and end any `Cursor` processes)
   - Open a regular Command Prompt or PowerShell and run:
     ```powershell
     "%LOCALAPPDATA%\Programs\cursor\Cursor.exe" --disable-gpu
     ```
   - If that works, make it permanent so you don't have to type this every time:
     - Find your Cursor shortcut on the Desktop or Start Menu
     - Right-click it → **Properties**
     - In the **Target** field, add ` --disable-gpu` at the very end (after the closing quote)
     - Example: `"C:\Users\Isiah\AppData\Local\Programs\cursor\Cursor.exe" --disable-gpu`
     - Click **OK**

3. **Clear the Cursor cache**
   - Close Cursor completely
   - Press `Win+R`, type `%APPDATA%\Cursor` and press Enter
   - Delete everything inside that folder
   - Relaunch Cursor

4. **Check antivirus / firewall**
   - Windows Defender, McAfee, Norton, etc. can block Cursor's UI from working
   - Try temporarily disabling your antivirus, then relaunch Cursor
   - If that fixes it, add Cursor to your antivirus exclusion list

5. **Full reinstall (nuclear option)**
   - Uninstall Cursor from **Settings → Apps**
   - Delete these folders:
     - `%APPDATA%\Cursor`
     - `%LOCALAPPDATA%\cursor-updater`
   - Download a fresh installer from [https://cursor.com](https://cursor.com)
   - Install and run as administrator

6. **Alternative install method**
   - Open PowerShell and run:
     ```powershell
     winget install Anysphere.Cursor
     ```

> **Note:** Make sure you're on **Windows 10 (version 1903+)** or **Windows 11**. Older versions can have compatibility issues.

### Cursor AI not responding
- Check your internet connection
- Verify your Cursor account is active and has available requests
- Try restarting Cursor (`Ctrl+Shift+P` → "Reload Window")

---

## Project Structure at a Glance

```
python/
├── pdf_generator/              # PDF generation GUI app
│   ├── gui.py                  #   Main GUI window
│   ├── pdf_generator.py        #   Entry point
│   ├── parsers.py              #   Data parsing logic
│   ├── html_builders.py        #   HTML template generation
│   ├── pdf_gen.py              #   PDF rendering (WeasyPrint)
│   ├── config.py               #   ★ Your agent info lives here
│   ├── referral_tracker.py     #   Referral management
│   ├── assets.py               #   Asset/image loading
│   ├── assets/                 #   Logos, headshot, images
│   └── referrals.db            #   Referral tracking database
│
├── underwriting/               # Underwriting risk assessment GUI
│   ├── underwriting_tool.py    #   Main application
│   ├── underwriting.db         #   Carrier guidelines database
│   └── assets/                 #   UI assets
│
├── password_vault/             # Secure password manager (Flask)
│   ├── app.py                  #   Flask web application
│   ├── vault.db                #   Encrypted password storage
│   └── requirements.txt        #   Flask + cryptography deps
│
├── landing/                    # Lead-capture landing page
│   ├── index.html              #   Multi-step form
│   └── form-to-sheet.gs        #   Google Apps Script handler
│
├── google_integrations/        # Gmail → Google Sheets automation
│   └── gmail_to_sheets_leadconduit.js
│
├── scripts/                    # Setup helper scripts
├── archive/                    # Old/test files
├── venv/                       # Python virtual environment (local)
├── .env.example                # API key template
├── .env                        # ★ Your API keys (git-ignored)
├── requirements.txt            # Core Python dependencies
└── README.md                   # Project documentation
```

---

## Quick-Start Checklist

Use this checklist to track your progress:

- [ ] Cursor IDE installed and signed in
- [ ] Python 3.10+ installed with PATH configured
- [ ] Git installed
- [ ] Repository cloned to your Desktop
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed
- [ ] `pip install -r password_vault\requirements.txt` completed
- [ ] WeasyPrint system dependencies installed (MSYS2 + PATH)
- [ ] `.env` file created with API key
- [ ] `config.py` updated with your agent info
- [ ] Agent headshot replaced in `pdf_generator/assets/`
- [ ] Cursor settings configured
- [ ] PDF Generator launches successfully
- [ ] Underwriting Tool launches successfully
- [ ] Password Vault launches successfully

---

## Need Help?

If you run into issues, open Cursor's AI chat (`Ctrl+L`) and describe the problem — it can read your code, check error messages, and help troubleshoot. That's the beauty of this setup.

You can also reach out to Brett directly.

---

*Welcome aboard, Isiah. Let's get to work.*
