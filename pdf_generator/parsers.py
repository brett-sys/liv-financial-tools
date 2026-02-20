"""Text parsing functions — extract structured data from pasted text."""

import re
import math


class ParseError(Exception):
    """Raised when parsing fails with a user-friendly message."""
    pass


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

    Raises ParseError if the input cannot be parsed at all.
    """
    if not data_text or not data_text.strip():
        raise ParseError("No data provided. Paste illustration data into the text area.")

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
                # Duplicate header row (e.g. repeated across pages) – skip it
                i += 1
                continue

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
                if len(remaining) >= 2:
                    extra_label = remaining[0]
                    extra_value = remaining[1]

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

                def parse_currency(val: str) -> float:
                    try:
                        cleaned = val.replace("$", "").replace(",", "").strip()
                        return float(cleaned) if cleaned else 0.0
                    except Exception:
                        return 0.0

                pairs: list[tuple[str, str]] = []

                if "Initial Face Amount" in raw_pairs:
                    pairs.append(
                        ("DEATH BENEFIT COVERAGE", raw_pairs["Initial Face Amount"])
                    )
                if "Modal Premium" in raw_pairs:
                    pairs.append(("MONTHLY PREMIUM", raw_pairs["Modal Premium"]))
                if "Minimum Premium (MMP)" in raw_pairs:
                    annual_min = parse_currency(raw_pairs["Minimum Premium (MMP)"])
                    monthly_min = annual_min / 12.0 if annual_min else 0.0
                    pairs.append(
                        (
                            "MIN MONTHLY PREMIUM",
                            f"${monthly_min:,.2f}" if monthly_min else raw_pairs["Minimum Premium (MMP)"],
                        )
                    )
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
                        '<div class="section section-no-break"><h2>Initial Policy Information</h2>'
                    )
                    html_parts.append('<div class="info-grid">')
                    for label, value in pairs:
                        html_parts.append('<div class="info-item">')
                        html_parts.append(f"<strong>{label}</strong>")
                        html_parts.append(f"<span>{value}</span>")
                        html_parts.append("</div>")
                    html_parts.append("</div>")

                if disclaimer_lines:
                    html_parts.append('<p class="note">')
                    html_parts.append(" ".join(disclaimer_lines))
                    html_parts.append("</p>")

                html_parts.append("</div>")
                html_parts.append("<!-- NLG_PLACEHOLDER -->")
                i = i
            else:
                pass

            continue

        # Skip Display Information section and related UI text entirely
        skip_phrases = [
            "Display Information",
            "View Option",
            "Current Illustrated",
            "Export to CSV",
            "Export to",
        ]
        if any(phrase in stripped_line for phrase in skip_phrases):
            i += 1
            if "Display Information" in stripped_line:
                while i < len(lines):
                    sub = lines[i].strip()
                    if not sub:
                        i += 1
                        continue
                    if "Initial Policy Information" in sub:
                        break
                    i += 1
            continue

        # Skip standalone "Values" heading (already handled by table parser)
        if stripped_line == "Values" or stripped_line.startswith("Values"):
            i += 1
            continue

        # Fallback: any other non-empty line before the docs
        if stripped_line:
            html_parts.append(f"<p>{stripped_line}</p>")
        i += 1

    if in_values_table:
        html_parts.append("</tbody></table></div>")

    result = "".join(html_parts)
    if not result.strip():
        raise ParseError(
            "Could not parse any illustration data from the pasted text.\n\n"
            "Expected input with sections like 'Initial Policy Information' and "
            "a 'Values' table with columns: Policy Year, Age, Premium Outlay, Accumulated Value."
        )
    return result
