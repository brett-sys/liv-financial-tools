"""HTML builder for Illustration Comparison PDF."""

import math
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as _cfg

COLORS = ["#4f8cff", "#ff8c00", "#34c759", "#af52de"]


def build_comparison_html(client_name, policies, logo_data_uri=None, agent_photo_data_uri=None):
    """Build a multi-page comparison PDF from parsed policy data.

    policies: list of dicts with keys:
        - label: str (e.g. "Option 1 – SummitLife")
        - summary: dict from parse_summary_data (or None)
        - graph: list of dicts from parse_graph_points
    """
    today = date.today().strftime("%B %d, %Y")
    n = len(policies)

    logo_html = ""
    if logo_data_uri:
        logo_html = f'<img src="{logo_data_uri}" style="height:50px;"/>'

    # -- Summary cards --
    cards_html = ""
    for i, p in enumerate(policies):
        s = p["summary"] or {}
        color = COLORS[i % len(COLORS)]
        cards_html += f"""
        <div style="flex:1; min-width:180px; background:#1a1d27; border:2px solid {color};
                    border-radius:12px; padding:16px; text-align:center;">
            <div style="font-weight:700; color:{color}; font-size:14px; margin-bottom:10px;">
                {p['label']}
            </div>
            <div style="margin-bottom:6px;">
                <div style="color:#8b8fa3; font-size:10px;">Death Benefit</div>
                <div style="font-size:16px; font-weight:700;">{s.get('death_benefit', '—')}</div>
            </div>
            <div style="margin-bottom:6px;">
                <div style="color:#8b8fa3; font-size:10px;">Annual Premium</div>
                <div style="font-size:14px; font-weight:600;">${s.get('annual_premium', 0):,.0f}</div>
            </div>
            <div style="margin-bottom:6px;">
                <div style="color:#8b8fa3; font-size:10px;">Breakeven</div>
                <div style="font-size:14px; font-weight:600;">
                    Year {s.get('breakeven_year', '—')} (Age {s.get('breakeven_age', '—')})
                </div>
            </div>
            <div>
                <div style="color:#8b8fa3; font-size:10px;">Final Cash Value (Year {s.get('last_year', '—')})</div>
                <div style="font-size:16px; font-weight:700; color:#34c759;">
                    ${s.get('last_cash', 0):,.0f}
                </div>
            </div>
        </div>
        """

    # -- Chart (SVG bar chart) --
    chart_svg = _build_comparison_chart(policies)

    # -- Year-by-year table --
    table_html = _build_comparison_table(policies)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    @page {{ size: letter; margin: 0.6in; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #e4e6eb; background: #0f1117; margin: 0; padding: 0; font-size: 12px;
    }}
    .header {{
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 2px solid #2a2e3a; padding-bottom: 12px; margin-bottom: 18px;
    }}
    .header-info {{ text-align: right; font-size: 10px; color: #8b8fa3; }}
    .section-title {{
        font-size: 16px; font-weight: 700; color: #e4e6eb;
        margin: 20px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #2a2e3a;
    }}
    .cards-row {{
        display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px;
    }}
    table {{
        width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 10px;
    }}
    th {{
        background: #1a1d27; color: #8b8fa3; padding: 6px 8px; text-align: center;
        border-bottom: 2px solid #2a2e3a; font-size: 9px; text-transform: uppercase;
    }}
    td {{
        padding: 5px 8px; text-align: center; border-bottom: 1px solid #1a1d27;
    }}
    tr:nth-child(even) {{ background: rgba(255,255,255,0.02); }}
    .page-break {{ page-break-before: always; }}
</style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div>{logo_html}</div>
        <div class="header-info">
            <strong style="color:#e4e6eb; font-size:14px;">Illustration Comparison</strong><br/>
            Prepared for: <strong style="color:#e4e6eb;">{client_name or 'Client'}</strong><br/>
            {today} &bull; {_cfg.AGENT_NAME} &bull; {_cfg.AGENT_PHONE}
        </div>
    </div>

    <!-- Summary Cards -->
    <div class="section-title">At a Glance</div>
    <div class="cards-row">{cards_html}</div>

    <!-- Chart -->
    <div class="section-title">Cash Value Growth Comparison</div>
    {chart_svg}

    <!-- Year-by-year table -->
    <div class="page-break"></div>
    <div class="section-title">Year-by-Year Comparison</div>
    {table_html}

    <div style="margin-top:20px; font-size:9px; color:#8b8fa3; text-align:center;">
        This comparison is for illustrative purposes only. Actual results will vary.<br/>
        {_cfg.AGENT_NAME} &bull; {_cfg.AGENT_PHONE} &bull; {_cfg.AGENT_WEBSITE}
    </div>
</body>
</html>"""
    return html


def _build_comparison_chart(policies):
    """Build a simple SVG bar chart comparing cash values at key years."""
    all_points = {}
    for i, p in enumerate(policies):
        for pt in p.get("graph", []):
            yr = pt["year"]
            if yr not in all_points:
                all_points[yr] = {}
            all_points[yr][i] = pt["cash_value"]

    if not all_points:
        return '<p style="color:#8b8fa3;">No chart data available.</p>'

    years = sorted(all_points.keys())
    max_val = max(
        val for yr_data in all_points.values() for val in yr_data.values()
    ) or 1

    n = len(policies)
    chart_w = 650
    chart_h = 220
    padding_l = 60
    padding_b = 30
    usable_w = chart_w - padding_l - 20
    usable_h = chart_h - padding_b - 10

    bar_group_w = usable_w / len(years)
    bar_w = max(8, (bar_group_w - 8) / n)

    bars = ""
    labels = ""
    for yi, yr in enumerate(years):
        group_x = padding_l + yi * bar_group_w
        labels += f'<text x="{group_x + bar_group_w / 2}" y="{chart_h - 5}" text-anchor="middle" fill="#8b8fa3" font-size="10">Yr {yr}</text>'
        for pi in range(n):
            val = all_points[yr].get(pi, 0)
            bar_h = (val / max_val) * usable_h if max_val else 0
            bx = group_x + 4 + pi * bar_w
            by = chart_h - padding_b - bar_h
            color = COLORS[pi % len(COLORS)]
            bars += f'<rect x="{bx}" y="{by}" width="{bar_w - 2}" height="{bar_h}" fill="{color}" rx="2"/>'

    # Y-axis labels
    y_labels = ""
    for i in range(5):
        val = max_val * i / 4
        y = chart_h - padding_b - (usable_h * i / 4)
        y_labels += f'<text x="{padding_l - 5}" y="{y + 3}" text-anchor="end" fill="#8b8fa3" font-size="9">${val:,.0f}</text>'
        y_labels += f'<line x1="{padding_l}" y1="{y}" x2="{chart_w - 20}" y2="{y}" stroke="#2a2e3a" stroke-width="0.5"/>'

    # Legend
    legend = ""
    for i, p in enumerate(policies):
        lx = padding_l + i * 150
        color = COLORS[i % len(COLORS)]
        legend += f'<rect x="{lx}" y="0" width="10" height="10" fill="{color}" rx="2"/>'
        legend += f'<text x="{lx + 14}" y="9" fill="#e4e6eb" font-size="10">{p["label"]}</text>'

    return f"""
    <svg width="{chart_w}" height="{chart_h + 20}" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(0, 15)">{legend}</g>
        <g transform="translate(0, 0)">{y_labels}{bars}{labels}</g>
    </svg>
    """


def _build_comparison_table(policies):
    """Build year-by-year HTML table comparing all policies."""
    # Gather all years from all policies
    all_years = set()
    policy_data = []
    for p in policies:
        yearly = {}
        for pt in p.get("graph", []):
            yearly[pt["year"]] = pt
            all_years.add(pt["year"])
        policy_data.append(yearly)

    if not all_years:
        return '<p style="color:#8b8fa3;">No year-by-year data available.</p>'

    years = sorted(all_years)

    # Table header
    header_cells = "<th>Year</th>"
    for i, p in enumerate(policies):
        color = COLORS[i % len(COLORS)]
        header_cells += f'<th style="color:{color};">{p["label"]}<br/>Premiums Paid</th>'
        header_cells += f'<th style="color:{color};">{p["label"]}<br/>Cash Value</th>'

    # Table rows
    rows = ""
    for yr in years:
        cells = f"<td><strong>{yr}</strong></td>"
        for i, pd in enumerate(policy_data):
            pt = pd.get(yr)
            if pt:
                cells += f'<td>${pt["premium_paid"]:,.0f}</td>'
                cells += f'<td style="font-weight:600;">${pt["cash_value"]:,.0f}</td>'
            else:
                cells += "<td>—</td><td>—</td>"
        rows += f"<tr>{cells}</tr>"

    return f"<table><thead><tr>{header_cells}</tr></thead><tbody>{rows}</tbody></table>"
