#!/usr/bin/env python3
"""
Simple PDF Generator - Just paste data and generate
"""

import json
import os
import tempfile
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import subprocess
import re
import base64
import math
from pathlib import Path

from dotenv import load_dotenv
from weasyprint import HTML as WeasyHTML

# Load .env from the project root (one level up from this script's folder)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# API Configuration (used by Business Card template only)
API_KEY = os.environ.get("APITEMPLATE_API_KEY", "")
API_ENDPOINT_TEMPLATE = "https://rest.apitemplate.io/v2/create-pdf"
POLICY_SUBMITTED_TEMPLATE_ID = "58777b23c9701b0e"
BUSINESS_CARD_TEMPLATE_ID = "f9177b23cf19f372"
LOGO_FILENAME = "assets/234.png"
NLG_LOGO_FILENAME = "assets/nlg_logo.png"

# Agent info (shown in PDF header) — update these with your real details
AGENT_NAME = "Brett Dunham"
AGENT_TITLE = "Agency Owner"
AGENT_PHONE = "(714) 335-1412"
AGENT_EMAIL = "brett@fflliv.com"
AGENT_LICENSE = "License #21114292"
AGENT_WEBSITE = "www.livfinancialgroup.com"
AGENT_PHOTO_FILENAME = "assets/agent_headshot.png"


def parse_policy_submitted_email(text: str) -> dict | None:
    """Parse policy details from email/confirmation text format.
    Extracts: Insured, Policy #, Insurance Product, Beneficiary, Face Amount,
    Monthly Premium, Monthly Draft. Returns dict for template or None if no match.
    """
    text = text.strip()
    if not text:
        return None

    def _re(group: int = 1):
        def _inner(pattern: str, flags=0):
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL | flags)
            return m.group(group).strip() if m else ""

        return _inner

    r = _re()
    insured = r(r"Insured:\s*(.+?)(?:\n|$)")
    policy_num = r(r"Policy\s*#?:\s*([A-Z0-9\-]+)")
    insurance_product = r(r"Insurance\s*Product:\s*(.+?)(?:\n|$)")
    beneficiary = r(r"Beneficiary:\s*(.+?)(?:\n|$)")
    face_amount = r(r"Face\s*Amount:\s*(\$?[\d,]+\.?\d*)")
    monthly_premium = r(r"Monthly\s*Premium:\s*(\$?[\d,]+\.?\d*)")
    monthly_draft = r(r"Monthly\s*Draft:\s*(.+?)(?:\n|$)")

    if not insured and not policy_num and not face_amount:
        return None

    # Extract carrier from product (e.g., "F & G - Everlast..." -> "F & G")
    carrier = ""
    if insurance_product and " - " in insurance_product:
        carrier = insurance_product.split(" - ")[0].strip()
    elif insurance_product:
        carrier = insurance_product

    # Format death benefit with $
    death_benefit = face_amount
    if death_benefit and not death_benefit.startswith("$"):
        death_benefit = f"${death_benefit}"

    # Calculate annual premium from monthly
    annual_premium = ""
    if monthly_premium:
        try:
            num = float(re.sub(r"[^\d.]", "", monthly_premium))
            annual_premium = f"${num * 12:,.2f}"
        except (ValueError, TypeError):
            annual_premium = "—"
    if not annual_premium:
        annual_premium = "—"

    # Format monthly premium with $
    if monthly_premium and not monthly_premium.startswith("$"):
        monthly_premium = f"${monthly_premium}"

    return {
        "client_name": insured or "—",
        "policy_number": policy_num or "—",
        "policy_type": insurance_product or "IUL",
        "carrier": carrier or "—",
        "effective_date": monthly_draft or "—",
        "death_benefit": death_benefit or "—",
        "beneficiary": beneficiary or "—",
        "annual_premium": annual_premium,
        "monthly_premium": monthly_premium or "—",
        "client_age": "—",
        "illustration_years": "—",
        "client_age_end": "—",
        "total_premiums": "—",
        "final_cash_value": "—",
        "breakeven_year": "—",
        "breakeven_age": "—",
    }


def load_logo_data_uri() -> str | None:
    """Load a local PNG logo and return a data: URI.

    Put the logo file next to this script (same folder) using the exact name in
    LOGO_FILENAME, and it will be embedded into the PDF header.
    """
    try:
        logo_path = Path(__file__).resolve().parent / LOGO_FILENAME
        if not logo_path.exists():
            return None
        data = logo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        # Assume PNG; you can change if you use JPG later.
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def load_nlg_logo_data_uri() -> str | None:
    """Load National Life Group PNG logo from script folder; return data URI or None if missing."""
    try:
        logo_path = Path(__file__).resolve().parent / NLG_LOGO_FILENAME
        if not logo_path.exists():
            return None
        data = logo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def load_agent_photo_data_uri() -> str | None:
    """Load agent headshot image and return a data: URI, or None if missing."""
    try:
        photo_path = Path(__file__).resolve().parent / AGENT_PHOTO_FILENAME
        if not photo_path.exists():
            return None
        data = photo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        # Detect format from extension
        suffix = photo_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def parse_graph_points(data_text: str) -> list[dict]:
    """Extract summary points for 'Cash Value vs Premiums Paid' style graph.

    Uses the Values table:
    - Cumulative Premium Outlay up to selected years
    - Accumulated Value at those years
    """
    lines = [line.rstrip() for line in data_text.strip().split("\n")]
    headers = None
    year_idx = premium_idx = acc_idx = None
    rows: list[dict] = []

    def split_fields(s: str) -> list[str]:
        if "\t" in s:
            return [p.strip() for p in s.split("\t") if p.strip()]
        parts = re.split(r"\s{2,}", s)
        return [p.strip() for p in parts if p.strip()]

    for line in lines:
        s = line.strip()
        if not s:
            continue

        # Detect header row of Values table
        if "Policy Year" in s and "Premium Outlay" in s and "Accumulated Value" in s:
            headers = split_fields(s)
            try:
                year_idx = headers.index("Policy Year")
                premium_idx = headers.index("Premium Outlay")
                acc_idx = headers.index("Accumulated Value")
            except ValueError:
                headers = None
            continue

        if headers is None:
            continue

        # Data rows start with a year number
        if not re.match(r"^\d+", s):
            # End of table
            break

        cells = split_fields(s)
        if len(cells) <= max(year_idx, premium_idx, acc_idx):
            continue

        try:
            year = int(cells[year_idx])
            prem_str = cells[premium_idx].replace("$", "").replace(",", "")
            acc_str = cells[acc_idx].replace("$", "").replace(",", "")
            premium = float(prem_str)
            acc_val = float(acc_str)
        except ValueError:
            continue

        rows.append({"year": year, "premium": premium, "acc": acc_val})

    if not rows:
        return []

    # Sort by year and compute cumulative premiums
    rows.sort(key=lambda r: r["year"])
    cumulative = 0.0
    by_year: dict[int, dict] = {}
    for r in rows:
        cumulative += r["premium"]
        by_year[r["year"]] = {
            "year": r["year"],
            "premium_paid": cumulative,
            "cash_value": r["acc"],
        }

    # Choose key horizons similar to 5/10/20/30/40 years
    candidate_years = [5, 10, 20, 30, 40]
    points: list[dict] = []
    for y in candidate_years:
        if y in by_year:
            points.append(by_year[y])

    # Fallback: if none of the standard horizons exist, pick up to 5 evenly spaced years
    if not points:
        all_years = sorted(by_year.keys())
        step = max(1, len(all_years) // 5)
        for idx in range(0, len(all_years), step):
            y = all_years[idx]
            points.append(by_year[y])
            if len(points) >= 5:
                break

    return points


def parse_summary_data(data_text: str) -> dict | None:
    """Extract numbers for the narrative 'Understanding Your Illustration' section."""
    lines = [line.rstrip() for line in data_text.strip().split("\n")]

    headers = None
    year_idx = age_idx = premium_idx = acc_idx = None
    rows: list[dict] = []

    def split_fields(s: str) -> list[str]:
        if "\t" in s:
            return [p.strip() for p in s.split("\t") if p.strip()]
        parts = re.split(r"\s{2,}", s)
        return [p.strip() for p in parts if p.strip()]

    # Parse Values table for year/age/premium/accumulated value
    for line in lines:
        s = line.strip()
        if not s:
            continue

        if (
            "Policy Year" in s
            and "Premium Outlay" in s
            and "Accumulated Value" in s
            and "Age" in s
        ):
            headers = split_fields(s)
            try:
                year_idx = headers.index("Policy Year")
                age_idx = headers.index("Age")
                premium_idx = headers.index("Premium Outlay")
                acc_idx = headers.index("Accumulated Value")
            except ValueError:
                headers = None
            continue

        if headers is None:
            continue

        if not re.match(r"^\d+", s):
            break

        cells = split_fields(s)
        if len(cells) <= max(year_idx, age_idx, premium_idx, acc_idx):
            continue

        try:
            year = int(cells[year_idx])
            age = int(cells[age_idx])
            prem_str = cells[premium_idx].replace("$", "").replace(",", "")
            acc_str = cells[acc_idx].replace("$", "").replace(",", "")
            premium = float(prem_str)
            acc_val = float(acc_str)
        except ValueError:
            continue

        rows.append(
            {"year": year, "age": age, "premium": premium, "acc": acc_val}
        )

    if not rows:
        return None

    rows.sort(key=lambda r: r["year"])
    start_age = rows[0]["age"]
    annual_premium = rows[0]["premium"]
    total_premiums = sum(r["premium"] for r in rows)
    last = rows[-1]
    last_year = last["year"]
    end_age = last["age"]
    last_cash = last["acc"]

    # Find first year where accumulated value exceeds cumulative premiums
    cumulative = 0.0
    breakeven_year = None
    breakeven_age = None
    for r in rows:
        cumulative += r["premium"]
        if r["acc"] >= cumulative:
            breakeven_year = r["year"]
            breakeven_age = r["age"]
            break

    # Get death benefit from Initial Face Amount if available
    death_benefit = ""
    for i, line in enumerate(lines):
        if "Initial Face Amount" in line:
            # next non-empty line should contain the amounts
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                cells = split_fields(lines[j])
                if cells:
                    death_benefit = cells[0]
            break

    return {
        "start_age": start_age,
        "end_age": end_age,
        "annual_premium": annual_premium,
        "total_premiums": total_premiums,
        "last_year": last_year,
        "last_cash": last_cash,
        "breakeven_year": breakeven_year,
        "breakeven_age": breakeven_age,
        "death_benefit": death_benefit,
    }


def parse_data_to_html(data_text):
    """Parse pasted data and convert to formatted HTML.

    Assumes the block always looks like the sample the user provided:
    - A 'Display Information' heading
    - An 'Initial Policy Information' block
    - A 'Values' header followed by the tab / space separated table
    - Followed by a bunch of APITemplate.io docs we want to ignore.
    """
    lines = [line.rstrip() for line in data_text.strip().split('\n')]
    html_parts = []

    i = 0
    in_values_table = False
    headers = []

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        # Stop once we hit the APITemplate docs / footer junk
        if (
            stripped_line.startswith("APITemplate.io")
            or stripped_line.startswith("APITemplate.io logo")
            or stripped_line.startswith("Search...")
            or stripped_line.startswith("Introduction")
        ):
            break

        if not stripped_line:
            i += 1
            continue

        # Detect Values table header
        if "Policy Year" in line and "Age" in line:
            if in_values_table:
                html_parts.append("</tbody></table></div>")

            html_parts.append('<div class="section"><h2>Policy Values</h2>')
            html_parts.append('<table class="data-table"><thead><tr>')

            # Parse headers - prioritize tabs
            if "\t" in line:
                headers = [h.strip() for h in line.split("\t") if h.strip()]
            else:
                headers = re.split(r"\s{2,}", line)
                headers = [h.strip() for h in headers if h.strip()]

            for h in headers:
                html_parts.append(f"<th>{h}</th>")

            html_parts.append("</tr></thead><tbody>")
            in_values_table = True
            i += 1
            continue

        # Process data rows
        if in_values_table:
            if re.match(r"^\d+", stripped_line):
                if "\t" in line:
                    cells = [c.strip() for c in line.split("\t") if c.strip()]
                else:
                    cells = re.split(r"\s{2,}", line)
                    cells = [c.strip() for c in cells if c.strip()]

                if len(cells) >= len(headers):
                    html_parts.append("<tr>")
                    for idx, cell in enumerate(cells[: len(headers)]):
                        # Right-align numeric / money columns (everything after Age)
                        if idx > 1 and (
                            cell.startswith("$")
                            or cell.endswith("%")
                            or re.match(r"^\d+", cell)
                        ):
                            html_parts.append(f'<td class="num">{cell}</td>')
                        else:
                            html_parts.append(f"<td>{cell}</td>")
                    html_parts.append("</tr>")
            else:
                # End of table; anything after will be ignored or treated as note
                html_parts.append("</tbody></table></div>")
                in_values_table = False
                if stripped_line and "Policy Year" not in stripped_line:
                    html_parts.append(f'<p class="note">{stripped_line}</p>')
            i += 1
            continue

        # Initial Policy Information section – turn selected fields into custom boxes
        if "Initial Policy Information" in line:
            # Collect all non-empty lines until we hit the Values header
            block_lines: list[str] = []
            i += 1
            while i < len(lines):
                info_line = lines[i].strip()
                if not info_line:
                    i += 1
                    continue
                if "Values" == info_line or info_line.startswith("Values"):
                    break
                block_lines.append(info_line)
                i += 1

            # Expect at least 4 lines (2 rows of labels + 2 rows of values)
            if len(block_lines) >= 4:
                def split_fields(s: str) -> list[str]:
                    if "\t" in s:
                        return [p.strip() for p in s.split("\t") if p.strip()]
                    parts = re.split(r"\s{2,}", s)
                    return [p.strip() for p in parts if p.strip()]

                labels_row1 = split_fields(block_lines[0])
                values_row1 = split_fields(block_lines[1])
                labels_row2 = split_fields(block_lines[2])
                values_row2 = split_fields(block_lines[3])

                extra_label = extra_value = None
                remaining = block_lines[4:]
                # Handle Guideline Single Premium / $52,657.00 pair when present
                if len(remaining) >= 2:
                    extra_label = remaining[0]
                    extra_value = remaining[1]

                # Optional: any further lines (like the agent-only disclaimer)
                disclaimer_lines = remaining[2:] if len(remaining) > 2 else []

                # Build flat list of (label, value) pairs from the raw rows
                raw_pairs: dict[str, str] = {}
                for idx, label in enumerate(labels_row1):
                    val = values_row1[idx] if idx < len(values_row1) else ""
                    if label:
                        raw_pairs[label] = val
                for idx, label in enumerate(labels_row2):
                    val = values_row2[idx] if idx < len(values_row2) else ""
                    if label:
                        raw_pairs[label] = val
                if extra_label and extra_value:
                    raw_pairs[extra_label] = extra_value

                # Helper to parse a currency string like "$1,035.60" to float
                def parse_currency(val: str) -> float:
                    try:
                        cleaned = val.replace("$", "").replace(",", "").strip()
                        return float(cleaned) if cleaned else 0.0
                    except Exception:
                        return 0.0

                # Build the final boxes we actually want to show, in order
                pairs: list[tuple[str, str]] = []

                # 1) Death Benefit Coverage (from Initial Face Amount)
                if "Initial Face Amount" in raw_pairs:
                    pairs.append(
                        ("DEATH BENEFIT COVERAGE", raw_pairs["Initial Face Amount"])
                    )

                # 2) Monthly Premium (from Modal Premium)
                if "Modal Premium" in raw_pairs:
                    pairs.append(("MONTHLY PREMIUM", raw_pairs["Modal Premium"]))

                # 3) Min Monthly Premium (Minimum Premium (MMP) / 12)
                if "Minimum Premium (MMP)" in raw_pairs:
                    annual_min = parse_currency(raw_pairs["Minimum Premium (MMP)"])
                    monthly_min = annual_min / 12.0 if annual_min else 0.0
                    pairs.append(
                        (
                            "MIN MONTHLY PREMIUM",
                            f"${monthly_min:,.2f}" if monthly_min else raw_pairs["Minimum Premium (MMP)"],
                        )
                    )

                # 4) Max Monthly Premium (MEC Premium / 12)
                if "MEC Premium" in raw_pairs:
                    annual_max = parse_currency(raw_pairs["MEC Premium"])
                    monthly_max = annual_max / 12.0 if annual_max else 0.0
                    pairs.append(
                        (
                            "MAX MONTHLY PREMIUM",
                            f"${monthly_max:,.2f}" if monthly_max else raw_pairs["MEC Premium"],
                        )
                    )

                if pairs:
                    html_parts.append(
                        '<div class="section"><h2>Initial Policy Information</h2>'
                    )
                    html_parts.append('<div class="info-grid">')
                    for label, value in pairs:
                        html_parts.append('<div class="info-item">')
                        html_parts.append(f"<strong>{label}</strong>")
                        html_parts.append(f"<span>{value}</span>")
                        html_parts.append("</div>")
                    html_parts.append("</div>")  # end info-grid

                if disclaimer_lines:
                    html_parts.append('<p class="note">')
                    html_parts.append(" ".join(disclaimer_lines))
                    html_parts.append("</p>")

            continue

        # Skip Display Information section entirely (user requested removal)
        if stripped_line.startswith("Display Information"):
            i += 1
            while i < len(lines):
                sub = lines[i].strip()
                if not sub:
                    i += 1
                    continue
                if "Initial Policy Information" in sub:
                    break
                i += 1
            continue

        # Fallback: any other non-empty line before the docs
        if stripped_line:
            html_parts.append(f"<p>{stripped_line}</p>")
        i += 1

    if in_values_table:
        html_parts.append("</tbody></table></div>")

    return "".join(html_parts)


def generate_pdf_html(
    html_body: str,
    logo_data_uri: str | None = None,
    graph_points: list[dict] | None = None,
    summary_data: dict | None = None,
    nlg_logo_data_uri: str | None = None,
    agent_photo_data_uri: str | None = None,
):
    """Create complete HTML document styled to match livfinancialgroup.com vibe."""
    logo_html = (
        f'<img class="logo" src="{logo_data_uri}" alt="LIV Financial Logo" />'
        if logo_data_uri
        else ""
    )
    nlg_logo_html = (
        f'<img class="logo logo-nlg" src="{nlg_logo_data_uri}" alt="National Life Group" />'
        if nlg_logo_data_uri
        else ""
    )

    # Build agent info HTML
    agent_photo_html = (
        f'<img class="agent-photo" src="{agent_photo_data_uri}" alt="{AGENT_NAME}" />'
        if agent_photo_data_uri
        else ""
    )
    agent_info_html = f"""
        <div class="agent-info">
            {agent_photo_html}
            <div class="agent-details">
                <div class="agent-name">{AGENT_NAME}</div>
                <div class="agent-detail">{AGENT_TITLE}</div>
                <div class="agent-detail">{AGENT_PHONE} | {AGENT_EMAIL}</div>
                <div class="agent-detail">{AGENT_LICENSE}</div>
                <div class="agent-detail">{AGENT_WEBSITE}</div>
            </div>
        </div>
    """

    # Build graph HTML if we have points
    graph_section_html = ""
    if graph_points:
        # Determine max value for relative bar heights
        max_val = max(
            max(p["premium_paid"], p["cash_value"]) for p in graph_points
            if p["premium_paid"] > 0 or p["cash_value"] > 0
        )
        max_val = max_val or 1.0  # avoid divide-by-zero

        # Choose 4 y-axis ticks (0, 1/3, 2/3, 1x max) and round to nice numbers
        def nice(n: float) -> float:
            if n <= 0:
                return 0.0
            exp = max(0, len(str(int(n))) - 2)
            step = 10 ** exp
            return math.ceil(n / step) * step

        top = nice(max_val)
        y_levels = [0.0, top * (1 / 3), top * (2 / 3), top]
        y_labels_html = []
        for v in y_levels:
            y_labels_html.append(f'<div class="cv-ylabel">${v:,.0f}</div>')

        cols_html = []
        for p in graph_points:
            year = p["year"]
            prem = p["premium_paid"]
            cv = p["cash_value"]
            prem_pct = (prem / top) * 100 if top else 0
            cv_pct = (cv / top) * 100 if top else 0
            prem_label = f"${prem:,.0f}"
            cv_label = f"${cv:,.0f}"

            cols_html.append(
                f"""
                <div class="cv-col">
                    <div class="cv-col-bars">
                        <div class="cv-bar-vertical cash" style="height:{cv_pct:.1f}%">
                            <span class="cv-value-label-vert">{cv_label}</span>
                        </div>
                        <div class="cv-bar-vertical premium" style="height:{prem_pct:.1f}%">
                            <span class="cv-value-label-vert">{prem_label}</span>
                        </div>
                    </div>
                    <div class="cv-year-label">{year}</div>
                </div>
                """
            )

        # Simple textual summary using the last point
        last_point = graph_points[-1]
        last_prem = f"${last_point['premium_paid']:,.0f}"
        last_cv = f"${last_point['cash_value']:,.0f}"
        last_year = last_point["year"]

        # Build narrative summary section if we have the extra data
        summary_html = ""
        if summary_data:
            start_age = summary_data["start_age"]
            end_age = summary_data["end_age"]
            annual_prem = f"${summary_data['annual_premium']:,.0f}"
            total_prem = f"${summary_data['total_premiums']:,.0f}"
            last_year = summary_data["last_year"]
            last_cash = f"${summary_data['last_cash']:,.0f}"
            death_benefit = summary_data.get("death_benefit") or "the illustrated amount"
            be_year = summary_data.get("breakeven_year")
            be_age = summary_data.get("breakeven_age")

            breakeven_sentence = ""
            if be_year is not None and be_age is not None:
                breakeven_sentence = (
                    f" Cash value first exceeds what you've put in at year {be_year} "
                    f"(age {be_age})."
                )

            summary_html = f"""
            <div class="summary-section">
                <h3>Understanding Your Illustration</h3>
                <p>
                    Your situation: This illustration is for someone age {start_age} at the start,
                    with a death benefit of {death_benefit} and an annual premium of {annual_prem}.
                    Over {last_year} years (through age {end_age}), you would pay a total of
                    {total_prem} in premiums. Under this non-guaranteed projection, the policy
                    cash value at year {last_year} is shown as {last_cash}.{breakeven_sentence}
                </p>
                <h3>How Indexed Universal Life (IUL) Works</h3>
                <p>
                    IUL is permanent life insurance that combines a death benefit with cash value
                    that can grow based on an index (for example, the S&amp;P 500). You pay premiums;
                    part goes to insurance and costs, and part can go to the cash value. The cash
                    value can be used later for loans, withdrawals, or retirement income.
                </p>
                <h3>Key Benefits</h3>
                <p><strong>Tax-advantaged growth:</strong> Cash value grows tax-deferred.</p>
                <p><strong>Death benefit:</strong> Your beneficiaries receive a tax-free death benefit.</p>
                <p><strong>Flexibility:</strong> You may adjust premiums (within limits) and access
                cash value via loans or withdrawals.</p>
                <p><strong>Protection from market downside in the index account:</strong>
                Indexed crediting can be 0% in down years but does not go negative.</p>
                <p class="note">
                    This is an overall summary prepared for clients. It is non-guaranteed and for
                    illustration purposes only—we are not claiming that these are exact or guaranteed
                    values. Non-guaranteed projections are hypothetical and may not apply to an actual
                    policy. If premium is not paid or is insufficient, monthly deductions will continue
                    against the policy value and additional premium may be required to keep the policy
                    in force. Actual results may be more or less favorable. Please see the guaranteed
                    projections and narrative summary. This is an illustration only, not an offer,
                    contract, or promise of future performance. Coverage is subject to the terms and
                    conditions of the issued policy.
                </p>
            </div>
            """

        graph_section_html = """
        <div class="cv-header">
            <div class="cv-title">Cash Value vs Premiums Paid</div>
            <div class="cv-legend">
                <span class="cv-dot premium"></span> Premiums paid
                <span class="cv-dot cash"></span> Cash value
            </div>
        </div>
        <div class="cv-body">
            <div class="cv-chart">
                <div class="cv-yaxis">
                    {y_labels}
                </div>
                <div class="cv-columns">
                    {cols}
                </div>
            </div>
            <div class="cv-xaxis-label">Years</div>
            <p class="cv-summary">
                By year {last_year}, total premiums paid are {last_prem} and the illustrated cash value is {last_cv}.
            </p>
            {summary_html}
        </div>
        """.format(
            y_labels="\n".join(y_labels_html),
            cols="\n".join(cols_html),
            last_year=last_year,
            last_prem=last_prem,
            last_cv=last_cv,
            summary_html=summary_html,
        )

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #e6f2f5;
            color: #123047;
            line-height: 1.6;
        }}
        .page {{
            width: 100%;
            max-width: 100%;
            margin: 0;
            background: #ffffff;
            border-radius: 0;
            overflow: hidden;
        }}
        .hero {{
            background: #0e7fa6;
            color: #ffffff;
            padding: 16px 36px 20px 36px;
        }}
        .hero-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .logo {{
            height: 80px;
            width: auto;
            max-width: 30%;
            border-radius: 0;
            background: transparent;
            padding: 0;
            display: block;
        }}
        .logo-nlg {{
            max-width: 30%;
            margin-left: auto;
        }}
        .agent-info {{
            display: flex;
            align-items: center;
            gap: 10px;
            text-align: left;
        }}
        .agent-photo {{
            width: 64px;
            height: 64px;
            border-radius: 50%;
            border: 2px solid #ffffff;
            object-fit: cover;
            flex-shrink: 0;
        }}
        .agent-details {{
            line-height: 1.3;
        }}
        .agent-name {{
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 2px;
        }}
        .agent-detail {{
            font-size: 10px;
            color: rgba(255, 255, 255, 0.9);
        }}
        .hero-title {{
            font-size: 22px;
            font-weight: 500;
            margin-bottom: 6px;
        }}
        .hero-subtitle {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            padding: 28px 32px 32px 32px;
        }}
        .section {{
            margin: 24px 0;
        }}
        .section h2 {{
            color: #0e7fa6;
            border-bottom: 2px solid #0e7fa6;
            padding-bottom: 6px;
            margin-bottom: 14px;
            font-size: 16px;
            font-weight: 600;
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0 4px 0;
            font-size: 11px;
        }}
        table.data-table thead {{
            background: #0e7fa6;
            color: #ffffff;
            /* prevent header from repeating on each PDF page so the table doesn't look duplicated */
            display: table-row-group;
        }}
        table.data-table th {{
            padding: 8px 6px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #d1e2ea;
        }}
        table.data-table td {{
            padding: 6px 6px;
            border: 1px solid #e0edf3;
        }}
        table.data-table td.num {{
            text-align: right;
            font-family: "Courier New", monospace;
        }}
        table.data-table tbody tr:nth-child(even) {{
            background-color: #f5fafc;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 14px;
            margin: 14px 0 4px 0;
        }}
        .info-item {{
            background: #ffffff;
            padding: 14px 16px;
            border: 1px solid #0e7fa6;
            border-radius: 6px;
            box-shadow: 0 1px 4px rgba(14, 127, 166, 0.12);
        }}
        .info-item strong {{
            display: block;
            color: #0e7fa6;
            margin-bottom: 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid #d1e2ea;
            padding-bottom: 6px;
        }}
        .info-item span {{
            color: #123047;
            font-size: 14px;
            font-weight: 600;
        }}
        p {{
            margin: 4px 0;
            font-size: 12px;
            color: #2c4a63;
        }}
        p.note {{
            color: #6b7f8f;
            font-style: italic;
            font-size: 11px;
            margin-top: 10px;
        }}
        /* Second-page graphs layout */
        .page-graphs {{
            page-break-before: always;
            padding: 32px 40px 40px 40px;
            background: #f5fafc;
            color: #123047;
        }}
        .cv-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }}
        .cv-title {{
            font-size: 18px;
            font-weight: 600;
            color: #0e7fa6;
        }}
        .cv-legend {{
            font-size: 11px;
            color: #476072;
            display: flex;
            gap: 14px;
            align-items: center;
        }}
        .cv-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            margin-right: 4px;
        }}
        .cv-dot.premium {{ background: #00e5ff; }}
        .cv-dot.cash {{ background: #11b6c8; }}
        .cv-body {{
            margin-top: 8px;
            border-radius: 10px;
            border: 1px solid #d1e2ea;
            padding: 18px 20px 22px 20px;
            background: #ffffff;
        }}
        .cv-chart {{
            display: flex;
            align-items: flex-end;
            gap: 10px;
        }}
        .cv-yaxis {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 180px;
            font-size: 10px;
            color: #476072;
            margin-right: 6px;
        }}
        .cv-ylabel {{
            text-align: right;
            min-width: 40px;
        }}
        .cv-columns {{
            display: flex;
            align-items: flex-end;
            gap: 18px;
            height: 210px;
        }}
        .cv-col {{
            flex: 1;
            text-align: center;
            font-size: 11px;
        }}
        .cv-col-bars {{
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 8px;
            height: 180px;
        }}
        .cv-bar-vertical {{
            position: relative;
            width: 18px;
            border-radius: 3px 3px 0 0;
        }}
        .cv-bar-vertical.premium {{
            background: #11b6c8;
        }}
        .cv-bar-vertical.cash {{
            background: #0e7fa6;
        }}
        .cv-value-label-vert {{
            position: absolute;
            top: -16px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 9px;
            font-weight: 600;
            color: #123047;
            white-space: nowrap;
        }}
        .cv-year-label {{
            margin-top: 6px;
            font-size: 11px;
            color: #476072;
        }}
        .cv-xaxis-label {{
            margin-top: 4px;
            font-size: 10px;
            color: #476072;
            text-align: right;
        }}
        .cv-summary {{
            margin-top: 6px;
            font-size: 10px;
            color: #697c8d;
        }}
        .summary-section {{
            margin-top: 14px;
            font-size: 11px;
            color: #2c4a63;
            line-height: 1.5;
        }}
        .summary-section h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #0e7fa6;
            margin: 8px 0 4px 0;
        }}
        .summary-section p {{
            margin: 4px 0;
        }}
        /* Living benefits summary page */
        .page-living {{
            page-break-before: always;
            padding: 40px 46px 44px 46px;
            background: #f5fafc;
            color: #123047;
            font-size: 12px;
        }}
        .lb-heading-main {{
            font-size: 24px;
            font-weight: 600;
            color: #0e7fa6;
            margin-bottom: 6px;
        }}
        .lb-heading-sub {{
            font-size: 14px;
            font-weight: 500;
            color: #14516f;
            margin-bottom: 18px;
        }}
        .lb-banner {{
            background: #0e7fa6;
            color: #ffffff;
            padding: 10px 16px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        .lb-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-top: 10px;
        }}
        .lb-card {{
            background: #ffffff;
            border-radius: 8px;
            border: 1px solid #d1e2ea;
            padding: 14px 16px 16px 16px;
        }}
        .lb-card h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #0e7fa6;
            margin-bottom: 6px;
        }}
        .lb-card p {{
            font-size: 12px;
            margin: 4px 0;
        }}
        .lb-icons-row {{
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }}
        .lb-icon {{
            flex: 1;
            border-radius: 8px;
            border: 1px solid #d1e2ea;
            padding: 10px 8px;
            text-align: center;
            color: #0e7fa6;
            font-size: 11px;
        }}
        .lb-icon-symbol {{
            font-size: 18px;
            margin-bottom: 4px;
        }}
        .lb-icon-symbol svg {{
            width: 32px;
            height: 24px;
        }}
        /* National Life Group section */
        .nlg-section {{
            padding: 24px 32px 32px 32px;
            border-top: 1px solid #d1e2ea;
            background: #f9fcfe;
        }}
        .nlg-section h2 {{
            color: #0e7fa6;
            border-bottom: 2px solid #0e7fa6;
            padding-bottom: 6px;
            margin-bottom: 14px;
            font-size: 16px;
            font-weight: 600;
        }}
        .nlg-section .nlg-story {{
            margin-bottom: 20px;
            font-size: 12px;
            color: #2c4a63;
            line-height: 1.6;
        }}
        .nlg-section .nlg-story p {{
            margin: 6px 0;
        }}
        .nlg-section .nlg-cols {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 16px;
        }}
        .nlg-section .nlg-col {{
            background: #e8f4f8;
            border-radius: 8px;
            padding: 14px 16px;
            border: 1px solid #d1e2ea;
        }}
        .nlg-section .nlg-col h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #0e7fa6;
            margin-bottom: 10px;
        }}
        .nlg-section .nlg-col p {{
            font-size: 11px;
            margin: 4px 0;
            color: #123047;
        }}
        .nlg-section .nlg-col .nlg-value {{
            font-weight: 600;
            color: #0e7fa6;
        }}
        .nlg-section .nlg-footnotes {{
            font-size: 10px;
            color: #6b7f8f;
            margin-top: 12px;
        }}
        @media print {{
            body {{
                background: #ffffff;
            }}
            .page {{
                margin: 0;
                border-radius: 0;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <header class="hero">
            <div class="hero-top">
                <span>{logo_html}</span>
                {agent_info_html}
                <span>{nlg_logo_html}</span>
            </div>
            <div class="hero-title">Policy Illustration Summary</div>
            <div class="hero-subtitle">
                Plan today, protect what matters most for a lifetime.
            </div>
        </header>
        <main class="content">
            {html_body}
        </main>
        <div class="nlg-section">
            <h2>National Life Group</h2>
            <div class="nlg-story">
                <p>At National Life Group, we are a mission-driven and purpose-filled business. For us, the cause of what we do is as important as the products we sell.</p>
                <p>And our cause is a very simple one, directed at the people who live and work on America&rsquo;s Main Streets: To Do Good in our communities and with the individuals we serve. Since 1848, we have aimed to keep our promises to provide stability in good times and in bad. And throughout that history, we have provided peace of mind to them as they plan their futures.</p>
            </div>
            <div class="nlg-cols">
                <div class="nlg-col">
                    <h3>Our Purpose</h3>
                    <p><strong>MISSION:</strong> <span class="nlg-value">Keeping our promises.</span></p>
                    <p><strong>VISION:</strong> To bring peace of mind to everyone we touch.</p>
                    <p><strong>VALUES:</strong> Do good. Be good. Make good.</p>
                </div>
                <div class="nlg-col">
                    <h3>Our Foundation</h3>
                    <p><span class="nlg-value">$57B</span> Total Assets&#185;</p>
                    <p><span class="nlg-value">$52B</span> Total Liabilities&#185;</p>
                    <p><span class="nlg-value">$3.9B</span> Total Benefits and Promises Kept&#178;</p>
                </div>
                <div class="nlg-col">
                    <h3>Strength and Stability</h3>
                    <p><span class="nlg-value">A+</span> (Superior) A.M. Best</p>
                    <p><span class="nlg-value">A+</span> (Strong) Standard &amp; Poor&rsquo;s</p>
                    <p><span class="nlg-value">A1</span> (Good) Moody&rsquo;s</p>
                </div>
            </div>
            <p class="nlg-footnotes">&#185; As of most recent reporting. &#178; Total benefits and promises kept.</p>
        </div>
    </div>
    <div class="page page-living">
        <div class="lb-heading-main">Living Benefits</div>
        <div class="lb-heading-sub">Benefits that can pay out while you’re alive if you experience a qualifying event.</div>
        <div class="lb-banner">Coverage in case of a qualifying illness or injury</div>
        <div class="lb-grid">
            <div class="lb-card">
                <h3>Terminal Illness</h3>
                <p>Access a portion of your death benefit early if you are diagnosed with a qualifying terminal illness and your life expectancy is limited.</p>
                <p>This benefit can help cover medical expenses, pay off debt, or support your family during a difficult time.</p>
            </div>
            <div class="lb-card">
                <h3>Chronic Illness</h3>
                <p>If you’re unable to perform basic activities of daily living or experience severe cognitive impairment, a portion of the benefit can be paid out while you are living.</p>
                <p>Funds can be used for caregiving, home modifications, or other support needs.</p>
            </div>
            <div class="lb-card">
                <h3>Critical Illness</h3>
                <p>Provides a lump-sum benefit after a qualifying diagnosis such as heart attack, stroke, cancer, or other major illnesses defined in the policy.</p>
                <p>Gives you financial flexibility during treatment and recovery.</p>
            </div>
            <div class="lb-card">
                <h3>Critical Injury</h3>
                <p>Helps cover expenses if you suffer a serious injury like paralysis, severe burns, or traumatic brain injury, subject to policy definitions.</p>
                <p>Benefits can be used for rehabilitation, lost income, or everyday bills.</p>
            </div>
        </div>
        <div class="lb-icons-row">
            <div class="lb-icon">
                <div class="lb-icon-symbol">❤</div>
                Terminal &amp; Chronic<br />Illness Support
            </div>
            <div class="lb-icon">
                <div class="lb-icon-symbol">➕</div>
                Critical Illness &amp;<br />Injury Protection
            </div>
            <div class="lb-icon">
                <div class="lb-icon-symbol">
                    <svg viewBox="0 0 36 24" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="9" cy="8" r="3" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                        <circle cx="19" cy="8" r="3" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                        <circle cx="14" cy="13" r="2.5" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                        <circle cx="24" cy="13" r="2.5" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                        <path d="M6 20 Q9 16 12 16 Q15 16 18 20" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                        <path d="M16 20 Q19 16 22 16 Q25 16 28 20" fill="none" stroke="#0e7fa6" stroke-width="1.5"/>
                    </svg>
                </div>
                Extra Safety Net for<br />You and Your Family
            </div>
        </div>
        <p class="note">
            This living benefits summary is for illustration only. Actual eligibility, covered conditions,
            and benefit amounts are determined by the specific policy contract.
        </p>
    </div>
    <div class="page page-graphs">
        {graph_section_html}
    </div>
</body>
</html>"""


def generate_pdf(html_content):
    """Generate PDF locally using WeasyPrint. Returns file:// URL to the PDF."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        WeasyHTML(string=html_content).write_pdf(pdf_path)
        return Path(pdf_path).resolve().as_uri()
    except Exception as e:
        raise Exception(f"WeasyPrint PDF generation failed: {e}") from e


def generate_pdf_from_template(template_id: str, data: dict) -> str:
    """Generate PDF from an API Template (e.g. business card). Returns download_url."""
    payload = {
        "template_id": template_id,
        "data": data,
    }
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
    }
    response = requests.post(API_ENDPOINT_TEMPLATE, json=payload, headers=headers, timeout=100)
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        raise Exception(result.get("message", "Unknown API error"))
    raise Exception(f"HTTP {response.status_code}: {response.text}")


POLICY_SUBMITTED_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>Policy Submitted Packet</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #e6f2f5;
      color: #123047;
      line-height: 1.6;
    }
    .page {
      width: 100%;
      max-width: 900px;
      margin: 24px auto;
      background: #ffffff;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    .hero {
      background: #0e7fa6;
      color: #ffffff;
      padding: 18px 32px;
    }
    .hero-top {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 10px;
    }
    .hero-logo {
      height: 60px;
      width: auto;
    }
    .hero-title {
      font-size: 26px;
      font-weight: 600;
    }
    .hero-subtitle {
      font-size: 14px;
      opacity: 0.9;
    }
    .content {
      padding: 24px 32px 32px 32px;
    }
    h2.section-title {
      font-size: 18px;
      color: #0e7fa6;
      border-bottom: 2px solid #0e7fa6;
      padding-bottom: 6px;
      margin-bottom: 16px;
      font-weight: 600;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .card {
      border: 1px solid #d1e2ea;
      border-radius: 8px;
      padding: 12px 14px;
      background: #f9fcfe;
    }
    .card-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #0e7fa6;
      font-weight: 600;
      margin-bottom: 4px;
      border-bottom: 1px solid #d1e2ea;
      padding-bottom: 4px;
    }
    .card-value {
      font-size: 14px;
      font-weight: 600;
      color: #123047;
      margin-top: 4px;
      word-wrap: break-word;
    }
    .note {
      font-size: 11px;
      color: #6b7f8f;
      margin-top: 6px;
    }
    .summary {
      margin-top: 10px;
      font-size: 12px;
      color: #2c4a63;
    }
    .summary h3 {
      font-size: 14px;
      font-weight: 600;
      color: #0e7fa6;
      margin: 10px 0 4px 0;
    }
    .summary p { margin: 4px 0; }
    .disclaimer {
      margin-top: 16px;
      font-size: 10px;
      color: #6b7f8f;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <div class="hero-top">
        {{logo_html}}
        <div class="hero-title">Policy Submitted</div>
      </div>
      <div class="hero-subtitle">
        Confirmation of coverage details for {{client_name}}.
      </div>
    </div>
    <div class="content">
      <h2 class="section-title">Policy Snapshot</h2>
      <div class="grid">
        <div class="card">
          <div class="card-label">Client Name</div>
          <div class="card-value">{{client_name}}</div>
        </div>
        <div class="card">
          <div class="card-label">Policy Number</div>
          <div class="card-value">{{policy_number}}</div>
        </div>
        <div class="card">
          <div class="card-label">Policy Type</div>
          <div class="card-value">{{policy_type}}</div>
        </div>
        <div class="card">
          <div class="card-label">Carrier</div>
          <div class="card-value">{{carrier}}</div>
        </div>
        <div class="card">
          <div class="card-label">Effective Date</div>
          <div class="card-value">{{effective_date}}</div>
        </div>
        <div class="card">
          <div class="card-label">Death Benefit</div>
          <div class="card-value">{{death_benefit}}</div>
        </div>
        <div class="card">
          <div class="card-label">Beneficiary</div>
          <div class="card-value">{{beneficiary}}</div>
        </div>
        <div class="card">
          <div class="card-label">Annual Premium</div>
          <div class="card-value">{{annual_premium}}</div>
        </div>
        <div class="card">
          <div class="card-label">Monthly Premium</div>
          <div class="card-value">{{monthly_premium}}</div>
        </div>
      </div>
      <div class="summary">
        <h3>Understanding Your Policy</h3>
        <p>
          This policy submitted packet confirms coverage for {{client_name}} with a death benefit of {{death_benefit}}
          and a monthly premium of {{monthly_premium}}. Your policy is with {{carrier}}.
        </p>
        <h3>How Indexed Universal Life (IUL) Works</h3>
        <p>
          IUL is permanent life insurance that combines a death benefit with cash value that can
          grow based on an index (for example, the S&amp;P 500). You pay premiums; part goes to
          insurance and costs, and part can go to the cash value. The cash value can be used
          later for loans, withdrawals, or supplemental retirement income.
        </p>
        <h3>Key Benefits</h3>
        <p><strong>Tax-advantaged growth:</strong> Cash value grows tax-deferred.</p>
        <p><strong>Death benefit protection:</strong> Your beneficiaries receive an income-tax-free benefit.</p>
        <p><strong>Flexibility:</strong> You may adjust premiums (within policy limits) and access cash value
        through loans or withdrawals.</p>
        <p><strong>Downside protection (index account):</strong> Indexed crediting can be 0% in down years
        but does not go negative.</p>
      </div>
      <div class="disclaimer">
        This policy submitted packet is for illustration purposes only and is not a contract.
        Non-guaranteed values are based on current assumptions and are subject to change.
        If premiums are not paid as illustrated, additional premiums may be required to keep the
        policy in force. Actual results may be more or less favorable. Please review your carrier's
        full policy and guaranteed values for complete details.
      </div>
    </div>
  </div>
</body>
</html>"""


def build_policy_submitted_html(payload: dict, logo_data_uri: str | None = None) -> str:
    """Build Policy Submitted HTML from parsed payload."""
    logo_html = ""
    if logo_data_uri:
        logo_html = f'<img class="hero-logo" src="{logo_data_uri}" alt="Logo" />'
    subs = {
        "{{logo_html}}": logo_html,
        "{{client_name}}": str(payload.get("client_name", "—")),
        "{{policy_number}}": str(payload.get("policy_number", "—")),
        "{{policy_type}}": str(payload.get("policy_type", "—")),
        "{{carrier}}": str(payload.get("carrier", "—")),
        "{{effective_date}}": str(payload.get("effective_date", "—")),
        "{{death_benefit}}": str(payload.get("death_benefit", "—")),
        "{{beneficiary}}": str(payload.get("beneficiary", "—")),
        "{{annual_premium}}": str(payload.get("annual_premium", "—")),
        "{{monthly_premium}}": str(payload.get("monthly_premium", "—")),
    }
    html = POLICY_SUBMITTED_HTML
    for k, v in subs.items():
        html = html.replace(k, v)
    return html


def open_chrome(url):
    """Open URL in Chrome"""
    try:
        subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', url])
        return True
    except:
        try:
            subprocess.Popen(['open', '-a', 'Google Chrome', url])
            return True
        except:
            subprocess.Popen(['open', url])
            return False


class SimplePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IUL Illustration")
        self.root.geometry("900x700")
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
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
            text="Generate IUL Illustration",
            command=self.generate,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=40,
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
            font=("Arial", 14, "bold"),
            padx=40,
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
            font=("Arial", 14, "bold"),
            padx=40,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.businesscard_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
    
    def generate(self):
        data = self.text_area.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please paste some data first!")
            return
        
        self.generate_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()
        
        try:
            # Parse and format HTML
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
            )
            
            # Generate PDF
            url = generate_pdf(html_content)
            
            # Open in Chrome
            open_chrome(url)
            
            messagebox.showinfo("Success", "PDF generated and opened in Chrome!")
            
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
                    "Error",
                    "Could not parse policy details.\n\n"
                    "Paste the full confirmation email/text (with Insured, Policy #, Face Amount, etc.)\n"
                    f"Or valid JSON.\n\n{e}",
                )
                return

        try:
            # Build Policy Submitted HTML and generate PDF via create-pdf-from-html
            logo_data_uri = load_logo_data_uri()
            html_content = build_policy_submitted_html(payload, logo_data_uri)
            url = generate_pdf(html_content)
            open_chrome(url)
            messagebox.showinfo("Success", "Policy Submitted PDF generated and opened in Chrome!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Policy Submitted PDF:\n{str(e)}")
        finally:
            self.policy_btn.config(state=tk.NORMAL, text="Policy Submitted")

    def generate_business_card(self):
        """Generate Business Card PDF using template f9177b23cf19f372."""
        data = self.text_area.get("1.0", tk.END).strip()
        default_data = {
            "name": "Your Name",
            "title": "Agent",
            "company": "LIV Financial",
            "phone": "(555) 123-4567",
            "email": "you@example.com",
            "website": "www.example.com",
        }
        if data:
            try:
                custom = json.loads(data)
                default_data.update(custom)
            except json.JSONDecodeError:
                pass
        data = default_data

        self.businesscard_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()
        try:
            url = generate_pdf_from_template(BUSINESS_CARD_TEMPLATE_ID, data)
            open_chrome(url)
            messagebox.showinfo("Success", "Business card PDF generated and opened in Chrome!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Business Card PDF:\n{str(e)}")
        finally:
            self.businesscard_btn.config(state=tk.NORMAL, text="Business Card")


def main():
    root = tk.Tk()
    app = SimplePDFApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
