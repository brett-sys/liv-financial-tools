# LIV Financial Tools — New Team Member Setup

> **Prepared by:** Brett Dunham
> **Last updated:** February 2026

This guide gets any new team member set up with the full LIV Financial toolkit. Follow every step in order — the whole process takes about 30 minutes.

---

## Table of Contents

1. [Install Cursor IDE](#1-install-cursor-ide)
2. [Install Python](#2-install-python)
3. [Install Git](#3-install-git)
4. [Clone the Repository](#4-clone-the-repository)
5. [Set Up the Python Environment](#5-set-up-the-python-environment)
6. [Install WeasyPrint Dependencies](#6-install-weasyprint-dependencies)
7. [Configure Environment Variables](#7-configure-environment-variables)
8. [Personalize Your Agent Info](#8-personalize-your-agent-info)
9. [Run the Tools](#9-run-the-tools)
10. [Verify Everything Works](#10-verify-everything-works)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Install Cursor IDE

Cursor is a VS Code-based editor with built-in AI. This is what we use for everything.

1. Go to [cursor.com](https://cursor.com)
2. Download the installer for your OS (Windows or Mac)
3. Run the installer and follow the prompts
4. Sign in or create a Cursor account

### Recommended Settings

Open the Command Palette and search for **"Preferences: Open User Settings (JSON)"**:

- **Windows:** `Ctrl+Shift+P`
- **Mac:** `Cmd+Shift+P`

Add these settings:

```json
{
    "window.commandCenter": true,
    "cursor.composer.shouldChimeAfterChatFinishes": true,
    "workbench.editor.enablePreview": false
}
```

### Recommended Extensions

Open Extensions (`Ctrl+Shift+X` / `Cmd+Shift+X`) and install:

| Extension | Purpose |
|-----------|---------|
| **Python** (Microsoft) | Python language support |
| **Pylance** (Microsoft) | Fast type checking and auto-complete |
| **SQLite Viewer** | View `.db` files in the editor |
| **GitLens** | Enhanced Git history |

---

## 2. Install Python

The tools require **Python 3.10 or newer**.

### Windows

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3.x installer
3. **Check the box: "Add Python to PATH"** (critical!)
4. Click "Install Now"

### Mac

Python 3 usually comes pre-installed. If not:

```bash
brew install python
```

### Verify

Open a terminal in Cursor (`` Ctrl+` `` or `` Cmd+` ``):

```bash
python --version      # Windows
python3 --version     # Mac
```

You should see `Python 3.10.x` or newer.

---

## 3. Install Git

### Windows

1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and run the installer (default options are fine)

### Mac

Git comes with Xcode Command Line Tools:

```bash
xcode-select --install
```

### Verify

```bash
git --version
```

---

## 4. Clone the Repository

Open a terminal in Cursor:

### Windows

```powershell
cd C:\Users\YOUR_USERNAME\Desktop
git clone <REPO_URL> python
cd python
```

### Mac

```bash
cd ~/Desktop
git clone <REPO_URL> python
cd python
```

> **Ask Brett for the repository URL.** If the repo is private, Brett will add you as a collaborator on GitHub.

---

## 5. Set Up the Python Environment

From the project root:

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r password_vault\requirements.txt
```

### Mac

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r password_vault/requirements.txt
```

> **Every time** you open a new terminal, activate the virtual environment first:
> - Windows: `venv\Scripts\activate`
> - Mac: `source venv/bin/activate`

---

## 6. Install WeasyPrint Dependencies

The PDF Generator uses WeasyPrint, which needs system libraries.

### Windows (MSYS2)

1. Download MSYS2 from [msys2.org](https://www.msys2.org/)
2. Install to the default path (`C:\msys64`)
3. Open **MSYS2 MINGW64** terminal and run:

```bash
pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-cairo mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-libffi
```

4. Add `C:\msys64\mingw64\bin` to your system PATH:
   - `Win+R` → type `sysdm.cpl` → **Advanced** → **Environment Variables**
   - Edit `Path` under System variables → add `C:\msys64\mingw64\bin`
   - Restart Cursor

### Mac (Homebrew)

```bash
bash scripts/install-weasyprint-deps.sh
```

Or manually:

```bash
brew install pango cairo gdk-pixbuf libffi
```

### Verify

```bash
python -c "import weasyprint; print('WeasyPrint OK')"
```

---

## 7. Configure Environment Variables

```bash
cp .env.example .env    # Mac
copy .env.example .env  # Windows
```

Open `.env` in Cursor. The only key you **must** fill in to get started is:

```
APITEMPLATE_API_KEY=your_key_here
```

> Ask Brett for the shared API key, or create your own at [apitemplate.io](https://apitemplate.io).

The other variables (GHL, Google Sheets, SMTP) are only needed for specific tools. Brett will help you configure those when the time comes.

---

## 8. Personalize Your Agent Info

### 8a. PDF Generator Config

Open `pdf_generator/config.py` and update these lines with **your** details:

```python
AGENT_NAME = "Your Full Name"
AGENT_TITLE = "Licensed Agent"
AGENT_PHONE = "(XXX) XXX-XXXX"
AGENT_EMAIL = "you@fflliv.com"
AGENT_LICENSE = "License #XXXXXXXX"
AGENT_WEBSITE = "www.livfinancialgroup.com"
```

### 8b. Replace Your Headshot

Replace `pdf_generator/assets/agent_headshot.png` with your professional headshot. Keep the same filename, or update `AGENT_PHOTO_FILENAME` in `config.py`.

### 8c. Business Card (Optional)

If you have a business card design, replace `pdf_generator/assets/business_card.png`.

---

## 9. Run the Tools

Make sure your virtual environment is activated first.

### Desktop Tools

| Tool | Command |
|------|---------|
| **PDF Generator** | `python -m pdf_generator` |
| **Underwriting Tool** | `python underwriting/underwriting_tool.py` |

### Web Tools

| Tool | Command | URL |
|------|---------|-----|
| **Agent Toolkit** | `python agent_toolkit/app.py` | [localhost:5055](http://localhost:5055) |
| **Password Vault** | `python -m password_vault` | [localhost:5050](http://localhost:5050) |
| **Lead Manager** | `python -m lead_manager` | [localhost:5070](http://localhost:5070) |

> The Password Vault will auto-open your browser. On first launch, you'll create a PIN.

---

## 10. Verify Everything Works

Run through this checklist:

- [ ] Cursor IDE installed and signed in
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] Repository cloned to Desktop
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed
- [ ] WeasyPrint dependencies installed
- [ ] `.env` file created with API key
- [ ] `config.py` updated with your agent info
- [ ] Headshot replaced in `pdf_generator/assets/`
- [ ] PDF Generator launches (`python -m pdf_generator`)
- [ ] Underwriting Tool launches (`python underwriting/underwriting_tool.py`)
- [ ] Password Vault launches (`python -m password_vault`)

---

## 11. Troubleshooting

### "python is not recognized" (Windows)
- Make sure you checked **"Add Python to PATH"** during installation
- Try `py` instead of `python`
- Restart Cursor

### WeasyPrint errors about missing libraries
- **Windows:** Make sure `C:\msys64\mingw64\bin` is in your system PATH, then restart Cursor
- **Mac:** Run `brew install pango cairo gdk-pixbuf libffi`
- Try: `pip install --force-reinstall weasyprint`

### "ModuleNotFoundError: No module named ..."
- Make sure your virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

### Database errors
Pull a fresh copy from the repo:
```bash
git checkout -- underwriting/underwriting.db
```

### tkinter not found (Windows)
Reinstall Python and make sure **"tcl/tk and IDLE"** is checked in optional features.

### Cursor UI frozen / buttons don't work (Windows)

Try these in order:

1. **Run as Administrator** — right-click Cursor → Run as administrator
2. **Disable GPU** — close Cursor, then run:
   ```powershell
   "%LOCALAPPDATA%\Programs\cursor\Cursor.exe" --disable-gpu
   ```
   To make it permanent, add `--disable-gpu` to the shortcut Target field.
3. **Clear cache** — delete everything in `%APPDATA%\Cursor`, relaunch
4. **Check antivirus** — temporarily disable, see if Cursor works, then add to exclusions
5. **Full reinstall** — uninstall, delete `%APPDATA%\Cursor` and `%LOCALAPPDATA%\cursor-updater`, reinstall

### Cursor AI not responding
- Check your internet connection
- Verify your Cursor account is active
- `Ctrl+Shift+P` → "Reload Window"

---

## Need Help?

Two options:

1. **Ask Cursor AI** — open the chat panel (`Ctrl+L` / `Cmd+L`) and describe your problem. It can read your code and help troubleshoot.
2. **Ask Brett** — reach out directly.

---

*Welcome to the team. Let's get to work.*
