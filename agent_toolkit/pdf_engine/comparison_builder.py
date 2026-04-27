"""HTML builder for Illustration Comparison PDF – styled to match Quote Comparison."""

import math
from datetime import date

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as _cfg

AGENT_NAME = _cfg.AGENT_NAME
AGENT_TITLE = _cfg.AGENT_TITLE
AGENT_PHONE = _cfg.AGENT_PHONE
AGENT_EMAIL = _cfg.AGENT_EMAIL_DISPLAY
AGENT_LICENSE = _cfg.AGENT_LICENSE
AGENT_WEBSITE = _cfg.AGENT_WEBSITE

BAR_SHADES = ["#0e7fa6", "#1a9fc4", "#74c0d8", "#b3dbe8"]


_DEFAULT_AGENT_INFO = {
    "name": AGENT_NAME,
    "title": AGENT_TITLE,
    "phone": AGENT_PHONE,
    "email": AGENT_EMAIL,
    "license": AGENT_LICENSE,
    "website": AGENT_WEBSITE,
}


def _resolve_agent(agent_info):
    if not agent_info:
        return _DEFAULT_AGENT_INFO
    merged = dict(_DEFAULT_AGENT_INFO)
    for k, v in agent_info.items():
        if v:
            merged[k] = v
    return merged


def build_comparison_html(client_name, policies, logo_data_uri=None, agent_photo_data_uri=None, agent_info=None):
    """Build a multi-page comparison PDF from parsed policy data.

    policies: list of dicts with keys:
        - label: str (e.g. "Option 1 – SummitLife")
        - summary: dict from parse_summary_data (or None)
        - graph: list of dicts from parse_graph_points
    """
    ai = _resolve_agent(agent_info)
    today = date.today().strftime("%B %d, %Y")
    n = len(policies)

    logo_html = ""
    if logo_data_uri:
        logo_html = f'<img class="logo" src="{logo_data_uri}" alt="LIV Financial Logo" />'

    agent_photo_html = ""
    if agent_photo_data_uri:
        agent_photo_html = f'<img class="agent-photo" src="{agent_photo_data_uri}" alt="{ai["name"]}" />'

    prepared_for_html = ""
    if client_name and client_name.strip():
        prepared_for_html = f'<div class="prepared-for">Prepared for <strong>{client_name.strip()}</strong></div>'

    # -- Summary stat boxes --
    stat_boxes_html = ""
    for i, p in enumerate(policies):
        s = p["summary"] or {}

        death_benefit = s.get("death_benefit", "—")
        annual_prem = f"${s['annual_premium']:,.0f}" if s.get("annual_premium") else "—"
        be_year = s.get("breakeven_year", "—")
        be_age = s.get("breakeven_age", "—")
        last_year = s.get("last_year", "—")
        last_cash = f"${s['last_cash']:,.0f}" if s.get("last_cash") else "—"

        stat_boxes_html += f"""
        <div class="stat-box">
            <div class="stat-label-title">{p['label']}</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">DEATH BENEFIT</div>
                    <div class="stat-value">{death_benefit}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">ANNUAL PREMIUM</div>
                    <div class="stat-value">{annual_prem}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">BREAKEVEN</div>
                    <div class="stat-value">Year {be_year} (Age {be_age})</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">CASH VALUE (YR {last_year})</div>
                    <div class="stat-value">{last_cash}</div>
                </div>
            </div>
        </div>"""

    # -- Chart --
    chart_svg = _build_comparison_chart(policies)

    # -- Year-by-year table --
    table_html = _build_comparison_table(policies)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    @page {{
        margin: 0.6in 0.5in 0.7in 0.5in;
        @bottom-center {{
            content: "Prepared by LIV Financial Group  |  {ai['license']}  |  Page " counter(page) " of " counter(pages);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 8px;
            color: #6b7f8f;
        }}
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #ffffff;
        color: #123047;
        line-height: 1.6;
        font-size: 12px;
    }}
    .hero {{
        background: #123047;
        color: #ffffff;
        padding: 18px 36px 22px 36px;
    }}
    .hero-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        border-bottom: none;
        padding-bottom: 14px;
    }}
    .hero-logo-wrap {{
        display: inline-block;
        background: transparent;
        padding: 0;
        border-radius: 0;
        line-height: 0;
    }}
    .logo {{ height: 56px; width: auto; max-width: 240px; display: block; }}
    .agent-info {{ display: flex; align-items: center; gap: 12px; text-align: left; }}
    .agent-photo {{
        width: 72px; height: 72px; border-radius: 6px;
        border: 2px solid rgba(255,255,255,0.6);
        object-fit: cover; object-position: top center; flex-shrink: 0;
    }}
    .agent-details {{ line-height: 1.35; }}
    .agent-name {{ font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 2px; }}
    .agent-detail {{ font-size: 10px; color: rgba(255,255,255,0.85); }}
    .hero-bottom {{ display: flex; justify-content: space-between; align-items: flex-end; }}
    .hero-title {{ font-size: 24px; font-weight: 400; letter-spacing: -0.01em; color: #fff; margin-bottom: 4px; }}
    .hero-subtitle {{ font-size: 13px; color: rgba(255,255,255,0.8); }}
    .prepared-for {{ font-size: 13px; color: rgba(255,255,255,0.95); margin-top: 6px; }}
    .prepared-for strong {{ font-weight: 700; }}
    .date-stamp {{ font-size: 10px; color: rgba(255,255,255,0.6); margin-top: 4px; }}
    .content {{ padding: 22px 36px 30px 36px; }}
    h2.section-title {{
        font-size: 16px;
        color: #123047;
        border-bottom: 2px solid #0e7fa6;
        padding-bottom: 5px;
        margin: 22px 0 14px 0;
        font-weight: 600;
    }}
    h2.section-title:first-child {{ margin-top: 0; }}
    .stat-boxes {{
        display: grid;
        grid-template-columns: repeat({min(n, 4)}, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }}
    .stat-box {{
        border: 1px solid #dde9f0;
        border-radius: 8px;
        padding: 14px 16px;
        background: #f4f9fc;
    }}
    .stat-label-title {{
        font-size: 14px;
        font-weight: 700;
        color: #123047;
        margin-bottom: 10px;
    }}
    .stat-grid {{
        display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
    }}
    .stat-label {{
        font-size: 8px; text-transform: uppercase; letter-spacing: 0.06em;
        color: #0e7fa6; font-weight: 700; margin-bottom: 2px;
    }}
    .stat-value {{ font-size: 14px; font-weight: 700; color: #123047; }}
    .chart-container {{
        background: #f4f9fc;
        border: 1px solid #dde9f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }}
    table.compare {{
        width: 100%; border-collapse: collapse; font-size: 10px; margin: 0 0 22px 0;
    }}
    table.compare thead {{ background: #123047; color: #fff; }}
    table.compare th {{
        padding: 8px 6px; text-align: center;
        font-weight: 600; font-size: 9px;
        text-transform: uppercase; letter-spacing: 0.04em;
    }}
    table.compare td {{
        padding: 7px 6px; text-align: center; border-bottom: 1px solid #dde9f0;
    }}
    table.compare tbody tr:nth-child(even) {{ background: #f4f9fc; }}
    table.compare td.num {{ font-weight: 600; }}
    table.compare td.year {{ font-weight: 700; color: #123047; }}
    .disclaimer {{
        margin-top: 20px; font-size: 9.5px; color: #6b7f8f; line-height: 1.55;
        border-top: 1px solid #dde9f0; padding-top: 10px;
    }}
    .page-break {{ page-break-before: always; }}
</style>
</head>
<body>
    <header class="hero">
        <div class="hero-top">
            <span class="hero-logo-wrap">{logo_html}</span>
            <div class="agent-info">
                {agent_photo_html}
                <div class="agent-details">
                    <div class="agent-name">{ai['name']}</div>
                    <div class="agent-detail">{ai['title']}</div>
                    <div class="agent-detail">{ai['phone']} | {ai['email']}</div>
                    <div class="agent-detail">{ai['license']}</div>
                    <div class="agent-detail">{ai['website']}</div>
                </div>
            </div>
        </div>
        <div class="hero-bottom">
            <div>
                <div class="hero-title">IUL Comparison</div>
                <div class="hero-subtitle">Side-by-side policy comparison</div>
                {prepared_for_html}
                <div class="date-stamp">{today}</div>
            </div>
        </div>
    </header>

    <div class="content">
        <h2 class="section-title">At a Glance</h2>
        <div class="stat-boxes">
            {stat_boxes_html}
        </div>

        <h2 class="section-title">Cash Value Growth Comparison</h2>
        <div class="chart-container">
            {chart_svg}
        </div>

        <div class="page-break"></div>
        <h2 class="section-title">Year-by-Year Comparison</h2>
        {table_html}

        <div class="disclaimer">
            This comparison is for illustrative purposes only and is not an offer or contract.
            Non-guaranteed projections are hypothetical and may not apply to an actual policy.
            Actual results may be more or less favorable. Please review each carrier&rsquo;s
            full illustration for guaranteed values and complete policy details.<br/>
            {ai['name']} &bull; {ai['phone']} &bull; {ai['website']}
        </div>
    </div>
</body>
</html>"""
    return html


def _build_comparison_chart(policies):
    """Build an SVG bar chart comparing cash values at key years."""
    all_points = {}
    for i, p in enumerate(policies):
        for pt in p.get("graph", []):
            yr = pt["year"]
            if yr not in all_points:
                all_points[yr] = {}
            all_points[yr][i] = pt["cash_value"]

    if not all_points:
        return '<p style="color:#6b7f8f;">No chart data available.</p>'

    years = sorted(all_points.keys())
    max_val = max(
        val for yr_data in all_points.values() for val in yr_data.values()
    ) or 1

    n = len(policies)
    chart_w = 620
    chart_h = 210
    padding_l = 65
    padding_b = 30
    usable_w = chart_w - padding_l - 20
    usable_h = chart_h - padding_b - 10

    bar_group_w = usable_w / len(years)
    bar_w = max(10, (bar_group_w - 10) / n)

    bars = ""
    labels = ""
    for yi, yr in enumerate(years):
        group_x = padding_l + yi * bar_group_w
        labels += (
            f'<text x="{group_x + bar_group_w / 2}" y="{chart_h - 5}" '
            f'text-anchor="middle" fill="#476072" font-size="10" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif">Yr {yr}</text>'
        )
        for pi in range(n):
            val = all_points[yr].get(pi, 0)
            bar_h = (val / max_val) * usable_h if max_val else 0
            bx = group_x + 4 + pi * bar_w
            by = chart_h - padding_b - bar_h
            shade = BAR_SHADES[pi % len(BAR_SHADES)]
            bars += f'<rect x="{bx}" y="{by}" width="{bar_w - 2}" height="{bar_h}" fill="{shade}" rx="3"/>'

    y_labels = ""
    for i in range(5):
        val = max_val * i / 4
        y = chart_h - padding_b - (usable_h * i / 4)
        y_labels += (
            f'<text x="{padding_l - 5}" y="{y + 3}" text-anchor="end" '
            f'fill="#476072" font-size="9" '
            f'font-family="-apple-system, BlinkMacSystemFont, sans-serif">${val:,.0f}</text>'
        )
        y_labels += (
            f'<line x1="{padding_l}" y1="{y}" x2="{chart_w - 20}" y2="{y}" '
            f'stroke="#dde9f0" stroke-width="1"/>'
        )

    legend = ""
    for i, p in enumerate(policies):
        lx = padding_l + i * 160
        shade = BAR_SHADES[i % len(BAR_SHADES)]
        legend += f'<rect x="{lx}" y="0" width="12" height="12" fill="{shade}" rx="3"/>'
        legend += (
            f'<text x="{lx + 16}" y="10" fill="#123047" font-size="11" '
            f'font-weight="600" font-family="-apple-system, BlinkMacSystemFont, sans-serif">'
            f'{p["label"]}</text>'
        )

    return f"""
    <svg width="{chart_w}" height="{chart_h + 22}" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(0, 16)">{legend}</g>
        <g transform="translate(0, 0)">{y_labels}{bars}{labels}</g>
    </svg>
    """


def _build_comparison_table(policies):
    """Build year-by-year HTML table comparing all policies."""
    all_years = set()
    policy_data = []
    for p in policies:
        yearly = {}
        for pt in p.get("graph", []):
            yearly[pt["year"]] = pt
            all_years.add(pt["year"])
        policy_data.append(yearly)

    if not all_years:
        return '<p style="color:#6b7f8f;">No year-by-year data available.</p>'

    years = sorted(all_years)

    header_cells = "<th>Year</th>"
    for i, p in enumerate(policies):
        header_cells += f'<th>{p["label"]}<br/>Premiums Paid</th>'
        header_cells += f'<th>{p["label"]}<br/>Cash Value</th>'

    rows = ""
    for yr in years:
        cells = f'<td class="year">{yr}</td>'
        for i, pd in enumerate(policy_data):
            pt = pd.get(yr)
            if pt:
                cells += f'<td class="num">${pt["premium_paid"]:,.0f}</td>'
                cells += f'<td class="num" style="font-weight:700;">${pt["cash_value"]:,.0f}</td>'
            else:
                cells += '<td>—</td><td>—</td>'
        rows += f"<tr>{cells}</tr>"

    return f'<table class="compare"><thead><tr>{header_cells}</tr></thead><tbody>{rows}</tbody></table>'
