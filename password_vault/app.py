"""
Password Vault - A simple, secure password manager web app.
Run with: python app.py
"""

import os
import json
import sqlite3
import hashlib
import base64
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, render_template_string
)
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DB_PATH = os.path.join(os.path.dirname(__file__), "vault.db")

CATEGORIES = [
    "Social Media",
    "Insurance Carriers",
    "Tools & Platforms",
    "Email Accounts",
    "Other",
]

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _derive_key(pin: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a PIN + salt using PBKDF2."""
    kdf_key = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000, dklen=32)
    return base64.urlsafe_b64encode(kdf_key)


def encrypt(plain: str, pin: str, salt: bytes) -> str:
    key = _derive_key(pin, salt)
    return Fernet(key).encrypt(plain.encode()).decode()


def decrypt(token: str, pin: str, salt: bytes) -> str:
    key = _derive_key(pin, salt)
    return Fernet(key).decrypt(token.encode()).decode()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entries (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            category  TEXT NOT NULL,
            title     TEXT NOT NULL,
            username  TEXT NOT NULL,
            password  TEXT NOT NULL,
            url       TEXT DEFAULT '',
            notes     TEXT DEFAULT '',
            created   TEXT NOT NULL,
            updated   TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def get_setting(key: str) -> str | None:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Routes – Auth
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login_page"))
    return redirect(url_for("vault"))


@app.route("/login")
def login_page():
    pin_hash = get_setting("pin_hash")
    is_setup = pin_hash is not None
    return render_template("login.html", is_setup=is_setup)


@app.route("/api/auth/setup", methods=["POST"])
def setup_pin():
    """First-time PIN creation."""
    if get_setting("pin_hash"):
        return jsonify({"error": "PIN already set"}), 400

    data = request.get_json()
    pin = data.get("pin", "")
    if len(pin) < 4:
        return jsonify({"error": "PIN must be at least 4 digits"}), 400

    salt = secrets.token_bytes(16)
    pin_hash = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000).hex()

    set_setting("pin_hash", pin_hash)
    set_setting("salt", salt.hex())

    session["authenticated"] = True
    session["pin"] = pin
    return jsonify({"ok": True})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    pin = data.get("pin", "")

    stored_hash = get_setting("pin_hash")
    salt = bytes.fromhex(get_setting("salt"))
    attempt_hash = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000).hex()

    if attempt_hash != stored_hash:
        return jsonify({"error": "Wrong PIN"}), 401

    session["authenticated"] = True
    session["pin"] = pin
    return jsonify({"ok": True})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Routes – Vault CRUD
# ---------------------------------------------------------------------------

@app.route("/vault")
@login_required
def vault():
    return render_template("vault.html", categories=CATEGORIES)


@app.route("/api/entries", methods=["GET"])
@login_required
def list_entries():
    conn = get_db()
    rows = conn.execute("SELECT * FROM entries ORDER BY category, title").fetchall()
    conn.close()

    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))

    entries = []
    for r in rows:
        entries.append({
            "id": r["id"],
            "category": r["category"],
            "title": r["title"],
            "username": decrypt(r["username"], pin, salt),
            "password": decrypt(r["password"], pin, salt),
            "url": r["url"],
            "notes": r["notes"],
            "created": r["created"],
            "updated": r["updated"],
        })
    return jsonify(entries)


@app.route("/api/entries", methods=["POST"])
@login_required
def create_entry():
    data = request.get_json()
    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))
    now = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        """INSERT INTO entries (category, title, username, password, url, notes, created, updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["category"],
            data["title"],
            encrypt(data["username"], pin, salt),
            encrypt(data["password"], pin, salt),
            data.get("url", ""),
            data.get("notes", ""),
            now, now,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201


@app.route("/api/entries/<int:entry_id>", methods=["PUT"])
@login_required
def update_entry(entry_id):
    data = request.get_json()
    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))
    now = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        """UPDATE entries
           SET category=?, title=?, username=?, password=?, url=?, notes=?, updated=?
           WHERE id=?""",
        (
            data["category"],
            data["title"],
            encrypt(data["username"], pin, salt),
            encrypt(data["password"], pin, salt),
            data.get("url", ""),
            data.get("notes", ""),
            now,
            entry_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_entry(entry_id):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Routes – Share via Email
# ---------------------------------------------------------------------------

@app.route("/api/share", methods=["POST"])
@login_required
def share_entry():
    """
    Share a specific entry via email.
    Uses mailto: link approach (opens user's default email client)
    so no SMTP config needed.
    """
    data = request.get_json()
    entry_id = data.get("entry_id")
    recipient = data.get("email", "")

    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))

    conn = get_db()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Entry not found"}), 404

    username = decrypt(row["username"], pin, salt)
    password = decrypt(row["password"], pin, salt)

    subject = f"Login Info: {row['title']}"
    body_lines = [
        f"Here are the login details for {row['title']}:",
        "",
        f"  Category: {row['category']}",
        f"  Username: {username}",
        f"  Password: {password}",
    ]
    if row["url"]:
        body_lines.append(f"  URL: {row['url']}")
    if row["notes"]:
        body_lines.append(f"  Notes: {row['notes']}")
    body_lines += ["", "Sent from Password Vault"]

    body = "\n".join(body_lines)

    return jsonify({
        "ok": True,
        "mailto": {
            "to": recipient,
            "subject": subject,
            "body": body,
        }
    })


# ---------------------------------------------------------------------------
# Routes – Export entry to file (for AirDrop / USB sharing)
# ---------------------------------------------------------------------------

@app.route("/api/export/<int:entry_id>", methods=["GET"])
@login_required
def export_entry(entry_id):
    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))

    conn = get_db()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Entry not found"}), 404

    username = decrypt(row["username"], pin, salt)
    password = decrypt(row["password"], pin, salt)

    lines = [
        f"{'='*40}",
        f"  LOGIN INFO: {row['title']}",
        f"{'='*40}",
        "",
        f"  Category:  {row['category']}",
        f"  Username:  {username}",
        f"  Password:  {password}",
    ]
    if row["url"]:
        lines.append(f"  URL:       {row['url']}")
    if row["notes"]:
        lines.append(f"  Notes:     {row['notes']}")
    lines += ["", f"{'='*40}", "  Shared from Password Vault", f"{'='*40}"]

    from flask import Response
    content = "\n".join(lines)
    safe_title = "".join(c for c in row["title"] if c.isalnum() or c in " -_").strip()
    filename = f"{safe_title} - Login.txt"

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ---------------------------------------------------------------------------
# Routes – Get plain text for clipboard copy
# ---------------------------------------------------------------------------

@app.route("/api/copytext/<int:entry_id>", methods=["GET"])
@login_required
def copy_text_entry(entry_id):
    pin = session["pin"]
    salt = bytes.fromhex(get_setting("salt"))

    conn = get_db()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Entry not found"}), 404

    username = decrypt(row["username"], pin, salt)
    password = decrypt(row["password"], pin, salt)

    lines = [
        f"{row['title']}",
        f"Username: {username}",
        f"Password: {password}",
    ]
    if row["url"]:
        lines.append(f"URL: {row['url']}")
    if row["notes"]:
        lines.append(f"Notes: {row['notes']}")

    return jsonify({"ok": True, "text": "\n".join(lines)})


# ---------------------------------------------------------------------------
# Routes – Change PIN
# ---------------------------------------------------------------------------

@app.route("/api/auth/change-pin", methods=["POST"])
@login_required
def change_pin():
    data = request.get_json()
    old_pin = data.get("old_pin", "")
    new_pin = data.get("new_pin", "")

    if len(new_pin) < 4:
        return jsonify({"error": "New PIN must be at least 4 digits"}), 400

    stored_hash = get_setting("pin_hash")
    old_salt = bytes.fromhex(get_setting("salt"))
    attempt_hash = hashlib.pbkdf2_hmac("sha256", old_pin.encode(), old_salt, 200_000).hex()

    if attempt_hash != stored_hash:
        return jsonify({"error": "Current PIN is incorrect"}), 401

    # Re-encrypt all entries with new key
    new_salt = secrets.token_bytes(16)
    conn = get_db()
    rows = conn.execute("SELECT * FROM entries").fetchall()

    for r in rows:
        username = decrypt(r["username"], old_pin, old_salt)
        password = decrypt(r["password"], old_pin, old_salt)
        conn.execute(
            "UPDATE entries SET username=?, password=? WHERE id=?",
            (
                encrypt(username, new_pin, new_salt),
                encrypt(password, new_pin, new_salt),
                r["id"],
            ),
        )

    conn.commit()
    conn.close()

    new_hash = hashlib.pbkdf2_hmac("sha256", new_pin.encode(), new_salt, 200_000).hex()
    set_setting("pin_hash", new_hash)
    set_setting("salt", new_salt.hex())

    session["pin"] = new_pin
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def open_browser():
    """Open the browser after a short delay to let the server start."""
    import time
    time.sleep(1.2)
    import webbrowser
    webbrowser.open("http://localhost:5050")


if __name__ == "__main__":
    import threading
    init_db()
    print("\n  Password Vault is running at: http://localhost:5050\n")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(port=5050)
