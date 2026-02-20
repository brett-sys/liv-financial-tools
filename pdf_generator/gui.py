"""Tkinter GUI — SimplePDFApp and main entry point."""

import json
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from urllib.parse import urlparse

from .assets import load_logo_data_uri, load_nlg_logo_data_uri, load_agent_photo_data_uri, load_business_card_data_uri
from .config import GHL_ENABLED
from .ghl_integration import send_to_ghl
from .parsers import (
    parse_policy_submitted_email,
    parse_graph_points,
    parse_summary_data,
    parse_data_to_html,
    ParseError,
)
from .html_builders import (
    generate_pdf_html,
    build_policy_submitted_html,
    build_business_card_html,
    build_quote_comparison_html,
)
from .pdf_gen import (
    generate_pdf,
    open_chrome,
    PDFGenerationError,
)
from .referral_tracker import ReferralTrackerWindow


class SimplePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IUL Illustration")
        self.root.geometry("900x700")
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # Client name input at top
        name_frame = tk.Frame(root, pady=8, padx=15)
        name_frame.pack(fill=tk.X)
        tk.Label(
            name_frame,
            text="Client Name:",
            font=("Arial", 12, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        self.client_name_var = tk.StringVar()
        self.client_name_entry = tk.Entry(
            name_frame,
            textvariable=self.client_name_var,
            font=("Arial", 12),
            width=35,
        )
        self.client_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # GHL integration row: email, phone, and send-to-GHL toggle
        ghl_frame = tk.Frame(root, pady=2, padx=15)
        ghl_frame.pack(fill=tk.X)

        tk.Label(
            ghl_frame, text="Email:", font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.client_email_var = tk.StringVar()
        tk.Entry(
            ghl_frame, textvariable=self.client_email_var,
            font=("Arial", 10), width=22,
        ).pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(
            ghl_frame, text="Phone:", font=("Arial", 10),
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.client_phone_var = tk.StringVar()
        tk.Entry(
            ghl_frame, textvariable=self.client_phone_var,
            font=("Arial", 10), width=14,
        ).pack(side=tk.LEFT, padx=(0, 12))

        self.ghl_var = tk.BooleanVar(value=GHL_ENABLED)
        self.ghl_check = tk.Checkbutton(
            ghl_frame,
            text="Send to Go High Level",
            variable=self.ghl_var,
            font=("Arial", 10, "bold"),
            fg="#0e7fa6",
            activeforeground="#0e7fa6",
            selectcolor="white",
        )
        self.ghl_check.pack(side=tk.LEFT, padx=(4, 0))

        # Text area - fills most of window
        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Courier", 11),
            padx=15,
            pady=15,
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.text_area.focus()

        # Buttons at bottom
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.generate_btn = tk.Button(
            btn_frame,
            text="IUL Illustration",
            command=self.generate,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.generate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.policy_btn = tk.Button(
            btn_frame,
            text="Policy Submitted",
            command=self.generate_policy_submitted,
            bg="#0e7fa6",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.policy_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        self.businesscard_btn = tk.Button(
            btn_frame,
            text="Business Card",
            command=self.generate_business_card,
            bg="#6b4c9a",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.businesscard_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        self.quote_btn = tk.Button(
            btn_frame,
            text="Quote Comparison",
            command=self.open_quote_comparison,
            bg="#e67e22",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.quote_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        self.referral_btn = tk.Button(
            btn_frame,
            text="Referral Tracker",
            command=self.open_referral_tracker,
            bg="#2c3e50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.referral_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

    def _sync_to_ghl(self, client_name: str, pdf_path: str):
        """Send the generated PDF to Go High Level in a background thread."""
        email = self.client_email_var.get().strip() or None
        phone = self.client_phone_var.get().strip() or None

        def _run():
            result = send_to_ghl(client_name, pdf_path, email=email, phone=phone)
            self.root.after(0, lambda: self._show_ghl_result(result))

        threading.Thread(target=_run, daemon=True).start()

    def _show_ghl_result(self, result: dict):
        """Show GHL sync result to the user (called on main thread)."""
        if result["success"]:
            messagebox.showinfo(
                "Go High Level",
                f"GHL sync complete:\n{result['message']}",
            )
        else:
            messagebox.showwarning(
                "Go High Level",
                f"GHL sync issue:\n{result['message']}",
            )

    def generate(self):
        data = self.text_area.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please paste some data first!")
            return

        self.generate_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()

        try:
            html_body = parse_data_to_html(data)
            logo_data_uri = load_logo_data_uri()
            nlg_logo_data_uri = load_nlg_logo_data_uri()
            agent_photo_data_uri = load_agent_photo_data_uri()
            graph_points = parse_graph_points(data)
            summary_data = parse_summary_data(data)
            html_content = generate_pdf_html(
                html_body,
                logo_data_uri=logo_data_uri,
                graph_points=graph_points,
                summary_data=summary_data,
                nlg_logo_data_uri=nlg_logo_data_uri,
                agent_photo_data_uri=agent_photo_data_uri,
                client_name=self.client_name_var.get(),
            )

            url = generate_pdf(html_content)
            open_chrome(url)
            messagebox.showinfo("Success", "PDF generated and opened in Chrome!")

            # Send to GHL if the checkbox is checked
            if self.ghl_var.get():
                pdf_path = urlparse(url).path
                self._sync_to_ghl(self.client_name_var.get(), pdf_path)

        except ParseError as e:
            messagebox.showerror("Parsing Error", str(e))
        except PDFGenerationError as e:
            messagebox.showerror("PDF Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="Generate IUL Illustration")

    def generate_policy_submitted(self):
        """Generate Policy Submitted PDF. Paste email/confirmation text or JSON."""
        data = self.text_area.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror(
                "Error",
                "Please paste your policy confirmation email/text for Policy Submitted.\n\n"
                "It should include lines like:\n"
                "Insured: [Name]\n"
                "Policy #: [Number]\n"
                "Insurance Product: [Product]\n"
                "Beneficiary: [Name]\n"
                "Face Amount: [Amount]\n"
                "Monthly Premium: [Amount]\n"
                "Monthly Draft: [Date]",
            )
            return

        self.policy_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()

        # Try email format first, then JSON
        payload = parse_policy_submitted_email(data)
        if payload is None:
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as e:
                self.policy_btn.config(state=tk.NORMAL, text="Policy Submitted")
                messagebox.showerror(
                    "Parsing Error",
                    "Could not parse policy details.\n\n"
                    "Paste the full confirmation email/text (with Insured, Policy #, Face Amount, etc.)\n"
                    f"Or valid JSON.\n\n{e}",
                )
                return

        try:
            logo_data_uri = load_logo_data_uri()
            html_content = build_policy_submitted_html(payload, logo_data_uri)
            url = generate_pdf(html_content)
            open_chrome(url)
            messagebox.showinfo("Success", "Policy Submitted PDF generated and opened in Chrome!")

            if self.ghl_var.get():
                client_name = payload.get("client_name", "").strip()
                if client_name and client_name != "—":
                    pdf_path = urlparse(url).path
                    self._sync_to_ghl(client_name, pdf_path)
        except PDFGenerationError as e:
            messagebox.showerror("PDF Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Policy Submitted PDF:\n{str(e)}")
        finally:
            self.policy_btn.config(state=tk.NORMAL, text="Policy Submitted")

    def generate_business_card(self):
        """Generate Business Card PDF from local business_card.png image."""
        self.businesscard_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()
        try:
            card_data_uri = load_business_card_data_uri()
            if not card_data_uri:
                messagebox.showerror("Error", "Business card image not found.\n\nPlace business_card.png in pdf_generator/assets/")
                return
            html_content = build_business_card_html(card_data_uri)
            url = generate_pdf(html_content)
            open_chrome(url)
            messagebox.showinfo("Success", "Business card PDF generated and opened in Chrome!")
        except PDFGenerationError as e:
            messagebox.showerror("PDF Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Business Card PDF:\n{str(e)}")
        finally:
            self.businesscard_btn.config(state=tk.NORMAL, text="Business Card")


    def open_quote_comparison(self):
        """Open the Quote Comparison input dialog."""
        QuoteComparisonDialog(self.root, parent_app=self)

    def open_referral_tracker(self):
        """Open the Referral Tracker window."""
        ReferralTrackerWindow(self.root)


# ---------------------------------------------------------------------------
# Quote Comparison Dialog
# ---------------------------------------------------------------------------

class QuoteComparisonDialog:
    """Pop-up form for entering carrier quotes, then generates a comparison PDF."""

    def __init__(self, parent, parent_app=None):
        self.parent_app = parent_app
        self.win = tk.Toplevel(parent)
        self.win.title("Quote Comparison")
        self.win.geometry("720x580")
        self.win.lift()
        self.win.attributes('-topmost', True)
        self.win.after_idle(self.win.attributes, '-topmost', False)

        # Client info
        client_frame = tk.LabelFrame(
            self.win, text="  Client Info  ",
            font=("Arial", 12, "bold"), fg="#0e7fa6",
            padx=12, pady=8,
        )
        client_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

        row = tk.Frame(client_frame)
        row.pack(fill=tk.X)
        tk.Label(row, text="Client Name:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.client_name_var = tk.StringVar()
        tk.Entry(row, textvariable=self.client_name_var, font=("Arial", 11), width=25).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(row, text="Age:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.client_age_var = tk.StringVar()
        tk.Entry(row, textvariable=self.client_age_var, font=("Arial", 11), width=6).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(row, text="Recommended #:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 4))
        self.rec_var = tk.StringVar(value="1")
        tk.Entry(row, textvariable=self.rec_var, font=("Arial", 11), width=4).pack(side=tk.LEFT)

        # Carrier entries (up to 4)
        self.carrier_frames = []
        self.carrier_vars = []

        carriers_frame = tk.Frame(self.win)
        carriers_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # Add scrollable canvas for carriers
        canvas = tk.Canvas(carriers_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(carriers_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.carriers_inner = tk.Frame(canvas)

        self.carriers_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.carriers_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i in range(4):
            self._add_carrier_row(i + 1)

        # Generate button
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill=tk.X, padx=12, pady=(6, 12))

        tk.Button(
            btn_frame,
            text="Generate Quote Comparison PDF",
            command=self._generate,
            bg="#e67e22",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=40,
            pady=12,
            relief=tk.FLAT,
            cursor="hand2",
        ).pack(fill=tk.X)

    def _add_carrier_row(self, num: int):
        """Add one carrier input section."""
        frame = tk.LabelFrame(
            self.carriers_inner,
            text=f"  Carrier {num}  ",
            font=("Arial", 11, "bold"),
            fg="#123047",
            padx=10,
            pady=6,
        )
        frame.pack(fill=tk.X, pady=4, padx=4)

        vars_dict = {}

        row1 = tk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Carrier:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["carrier"] = tk.StringVar()
        tk.Entry(row1, textvariable=vars_dict["carrier"], font=("Arial", 10), width=18).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(row1, text="Product:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["product"] = tk.StringVar()
        tk.Entry(row1, textvariable=vars_dict["product"], font=("Arial", 10), width=22).pack(side=tk.LEFT)

        row2 = tk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)

        tk.Label(row2, text="Monthly Premium:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["monthly_premium"] = tk.StringVar()
        tk.Entry(row2, textvariable=vars_dict["monthly_premium"], font=("Arial", 10), width=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(row2, text="Death Benefit:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["death_benefit"] = tk.StringVar()
        tk.Entry(row2, textvariable=vars_dict["death_benefit"], font=("Arial", 10), width=12).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(row2, text="10-Yr Cash Value:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["cash_value_10yr"] = tk.StringVar()
        tk.Entry(row2, textvariable=vars_dict["cash_value_10yr"], font=("Arial", 10), width=12).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(row2, text="Rating:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 4))
        vars_dict["rating"] = tk.StringVar()
        tk.Entry(row2, textvariable=vars_dict["rating"], font=("Arial", 10), width=10).pack(side=tk.LEFT)

        self.carrier_vars.append(vars_dict)

    def _generate(self):
        """Collect data and generate the PDF."""
        client_name = self.client_name_var.get().strip()
        if not client_name:
            messagebox.showerror("Error", "Please enter a client name.", parent=self.win)
            return

        # Collect carriers that have at least a name
        carriers = []
        for v in self.carrier_vars:
            carrier_name = v["carrier"].get().strip()
            if carrier_name:
                carriers.append({
                    "carrier": carrier_name,
                    "product": v["product"].get().strip() or "—",
                    "monthly_premium": v["monthly_premium"].get().strip() or "—",
                    "death_benefit": v["death_benefit"].get().strip() or "—",
                    "cash_value_10yr": v["cash_value_10yr"].get().strip() or "—",
                    "rating": v["rating"].get().strip() or "—",
                })

        if not carriers:
            messagebox.showerror("Error", "Enter at least one carrier.", parent=self.win)
            return

        # Parse recommended index
        recommended_idx = None
        try:
            rec_num = int(self.rec_var.get().strip())
            if 1 <= rec_num <= len(carriers):
                recommended_idx = rec_num - 1
        except (ValueError, TypeError):
            pass

        try:
            logo_data_uri = load_logo_data_uri()
            agent_photo_data_uri = load_agent_photo_data_uri()

            html_content = build_quote_comparison_html(
                client_name=client_name,
                client_age=self.client_age_var.get().strip(),
                carriers=carriers,
                recommended_idx=recommended_idx,
                logo_data_uri=logo_data_uri,
                agent_photo_data_uri=agent_photo_data_uri,
            )

            url = generate_pdf(html_content)
            open_chrome(url)
            messagebox.showinfo("Success", "Quote Comparison PDF generated!", parent=self.win)

            if self.parent_app and self.parent_app.ghl_var.get():
                pdf_path = urlparse(url).path
                self.parent_app._sync_to_ghl(client_name, pdf_path)

        except PDFGenerationError as e:
            messagebox.showerror("PDF Error", str(e), parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}", parent=self.win)


def main():
    root = tk.Tk()
    app = SimplePDFApp(root)
    root.mainloop()
