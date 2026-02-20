"""Referral Tracker — SQLite-backed referral management with tkinter GUI."""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from pathlib import Path

from .config import PACKAGE_DIR

DB_PATH = PACKAGE_DIR / "referrals.db"

STATUSES = ["New", "Contacted", "Quoted", "Applied", "Sold", "Lost"]


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the referrals database, creating it if needed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_name TEXT NOT NULL,
            referred_name TEXT NOT NULL,
            referred_phone TEXT DEFAULT '',
            referred_email TEXT DEFAULT '',
            date_added TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            notes TEXT DEFAULT '',
            premium_sold TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def add_referral(referrer_name: str, referred_name: str, phone: str = "",
                 email: str = "", notes: str = "") -> int:
    """Insert a new referral. Returns the new row id."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    today = date.today().isoformat()
    cur = conn.execute(
        "INSERT INTO referrals (referrer_name, referred_name, referred_phone, "
        "referred_email, date_added, status, notes, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'New', ?, ?)",
        (referrer_name, referred_name, phone, email, today, notes, now),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_all_referrals() -> list[dict]:
    """Return all referrals sorted by most recent first."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM referrals ORDER BY date_added DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_status(row_id: int, new_status: str, premium: str = ""):
    """Update a referral's status (and optionally premium_sold)."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    if premium:
        conn.execute(
            "UPDATE referrals SET status=?, premium_sold=?, updated_at=? WHERE id=?",
            (new_status, premium, now, row_id),
        )
    else:
        conn.execute(
            "UPDATE referrals SET status=?, updated_at=? WHERE id=?",
            (new_status, now, row_id),
        )
    conn.commit()
    conn.close()


def delete_referral(row_id: int):
    """Delete a referral by id."""
    conn = _get_conn()
    conn.execute("DELETE FROM referrals WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Return summary stats."""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM referrals").fetchone()[0]
    sold = conn.execute("SELECT COUNT(*) FROM referrals WHERE status='Sold'").fetchone()[0]
    lost = conn.execute("SELECT COUNT(*) FROM referrals WHERE status='Lost'").fetchone()[0]

    # Top referrers
    top = conn.execute(
        "SELECT referrer_name, COUNT(*) as cnt FROM referrals "
        "GROUP BY referrer_name ORDER BY cnt DESC LIMIT 5"
    ).fetchall()

    # Thank-you reminders (sold referrals)
    thankyou = conn.execute(
        "SELECT referrer_name, referred_name FROM referrals WHERE status='Sold' "
        "ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()

    conn.close()

    conversion = (sold / total * 100) if total > 0 else 0
    closed_total = sold + lost
    close_rate = (sold / closed_total * 100) if closed_total > 0 else 0

    return {
        "total": total,
        "sold": sold,
        "lost": lost,
        "conversion_pct": conversion,
        "close_rate_pct": close_rate,
        "top_referrers": [(r[0], r[1]) for r in top],
        "thankyou_list": [(r[0], r[1]) for r in thankyou],
    }


# ---------------------------------------------------------------------------
# Tkinter GUI
# ---------------------------------------------------------------------------

class ReferralTrackerWindow:
    """Separate top-level window for the Referral Tracker."""

    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Referral Tracker")
        self.win.geometry("960x650")
        self.win.lift()
        self.win.attributes('-topmost', True)
        self.win.after_idle(self.win.attributes, '-topmost', False)

        # ------ Top: Add Referral Form ------
        form_frame = tk.LabelFrame(
            self.win, text="  Add New Referral  ",
            font=("Arial", 12, "bold"), fg="#0e7fa6",
            padx=12, pady=8,
        )
        form_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

        row1 = tk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Referrer:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.referrer_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.referrer_var, font=("Arial", 11), width=20).pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(row1, text="Referred Person:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.referred_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.referred_var, font=("Arial", 11), width=20).pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(row1, text="Phone:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.phone_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.phone_var, font=("Arial", 11), width=14).pack(side=tk.LEFT)

        row2 = tk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=2)

        tk.Label(row2, text="Email:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.email_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.email_var, font=("Arial", 11), width=24).pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(row2, text="Notes:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.notes_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.notes_var, font=("Arial", 11), width=30).pack(side=tk.LEFT, padx=(0, 12))

        add_btn = tk.Button(
            row2, text="Add Referral", command=self._add_referral,
            bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
            padx=16, pady=4, relief=tk.FLAT, cursor="hand2",
        )
        add_btn.pack(side=tk.RIGHT)

        # ------ Middle: Referral List ------
        list_frame = tk.Frame(self.win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        cols = ("id", "date", "referrer", "referred", "phone", "status", "premium", "notes")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=12)

        col_config = {
            "id": ("ID", 40),
            "date": ("Date", 85),
            "referrer": ("Referrer", 130),
            "referred": ("Referred Person", 140),
            "phone": ("Phone", 110),
            "status": ("Status", 80),
            "premium": ("Premium", 80),
            "notes": ("Notes", 200),
        }
        for col, (heading, width) in col_config.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=40)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ------ Action buttons row ------
        action_frame = tk.Frame(self.win)
        action_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        tk.Label(action_frame, text="Change Status:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        self.status_combo = ttk.Combobox(
            action_frame, values=STATUSES, state="readonly", width=12, font=("Arial", 10),
        )
        self.status_combo.pack(side=tk.LEFT, padx=(0, 4))
        self.status_combo.set("Contacted")

        tk.Label(action_frame, text="Premium:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        self.premium_var = tk.StringVar()
        tk.Entry(action_frame, textvariable=self.premium_var, font=("Arial", 10), width=10).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            action_frame, text="Update Selected", command=self._update_status,
            bg="#0e7fa6", fg="white", font=("Arial", 10, "bold"),
            padx=12, relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            action_frame, text="Delete Selected", command=self._delete_selected,
            bg="#c0392b", fg="white", font=("Arial", 10, "bold"),
            padx=12, relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            action_frame, text="Refresh", command=self._refresh_list,
            bg="#476072", fg="white", font=("Arial", 10, "bold"),
            padx=12, relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.LEFT)

        tk.Button(
            action_frame, text="View Stats", command=self._show_stats,
            bg="#6b4c9a", fg="white", font=("Arial", 10, "bold"),
            padx=12, relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.RIGHT)

        # ------ Load data ------
        self._refresh_list()

    def _add_referral(self):
        referrer = self.referrer_var.get().strip()
        referred = self.referred_var.get().strip()
        if not referrer or not referred:
            messagebox.showerror("Error", "Referrer and Referred Person are required.", parent=self.win)
            return

        add_referral(
            referrer_name=referrer,
            referred_name=referred,
            phone=self.phone_var.get().strip(),
            email=self.email_var.get().strip(),
            notes=self.notes_var.get().strip(),
        )

        # Clear form
        self.referrer_var.set("")
        self.referred_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.notes_var.set("")

        self._refresh_list()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        referrals = get_all_referrals()
        for r in referrals:
            self.tree.insert("", tk.END, values=(
                r["id"],
                r["date_added"],
                r["referrer_name"],
                r["referred_name"],
                r["referred_phone"],
                r["status"],
                r["premium_sold"] or "",
                r["notes"],
            ))

    def _update_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a referral from the list first.", parent=self.win)
            return

        new_status = self.status_combo.get()
        premium = self.premium_var.get().strip()

        for item in selected:
            row_id = self.tree.item(item)["values"][0]
            update_status(row_id, new_status, premium)

        self.premium_var.set("")
        self._refresh_list()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a referral from the list first.", parent=self.win)
            return

        if not messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} referral(s)?", parent=self.win):
            return

        for item in selected:
            row_id = self.tree.item(item)["values"][0]
            delete_referral(row_id)

        self._refresh_list()

    def _show_stats(self):
        stats = get_stats()

        top_lines = "\n".join(
            f"  {name}: {count} referral(s)" for name, count in stats["top_referrers"]
        ) or "  No referrals yet"

        thankyou_lines = "\n".join(
            f"  Thank {referrer} (referred {referred} - SOLD!)"
            for referrer, referred in stats["thankyou_list"]
        ) or "  No sold referrals yet"

        msg = (
            f"REFERRAL STATS\n"
            f"{'='*35}\n\n"
            f"Total Referrals:  {stats['total']}\n"
            f"Sold:             {stats['sold']}\n"
            f"Lost:             {stats['lost']}\n"
            f"Conversion Rate:  {stats['conversion_pct']:.1f}%\n"
            f"Close Rate:       {stats['close_rate_pct']:.1f}%\n"
            f"  (sold / (sold + lost))\n\n"
            f"TOP REFERRERS\n"
            f"{'-'*35}\n"
            f"{top_lines}\n\n"
            f"THANK-YOU REMINDERS\n"
            f"{'-'*35}\n"
            f"{thankyou_lines}"
        )

        messagebox.showinfo("Referral Stats", msg, parent=self.win)
