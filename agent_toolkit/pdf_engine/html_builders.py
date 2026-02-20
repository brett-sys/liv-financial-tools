"""HTML template construction for all PDF types."""

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


def generate_pdf_html(
    html_body: str,
    logo_data_uri: str | None = None,
    graph_points: list[dict] | None = None,
    summary_data: dict | None = None,
    nlg_logo_data_uri: str | None = None,
    agent_photo_data_uri: str | None = None,
    client_name: str = "",
):
    """Create complete HTML document styled to match livfinancialgroup.com vibe."""
    # Inject NLG company info into html_body at the placeholder
    nlg_section_html = """
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
    """
    html_body = html_body.replace("<!-- NLG_PLACEHOLDER -->", nlg_section_html)

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
        y_levels = [top, top * (2 / 3), top * (1 / 3), 0.0]
        y_labels_html = []
        for v in y_levels:
            y_labels_html.append(f'<div class="cv-ylabel">${v:,.0f}</div>')

        cols_html = []
        xlabels_html = []
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
                    <div class="cv-bar-vertical cash" style="height:{cv_pct:.1f}%">
                        <span class="cv-value-label-vert">{cv_label}</span>
                    </div>
                    <div class="cv-bar-vertical premium" style="height:{prem_pct:.1f}%">
                        <span class="cv-value-label-vert">{prem_label}</span>
                    </div>
                </div>
                """
            )
            xlabels_html.append(f'<div class="cv-xlbl">{year}</div>')

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
            <div class="cv-chart-area">
                <div class="cv-yaxis">
                    {y_labels}
                </div>
                <div class="cv-columns">
                    {cols}
                </div>
            </div>
            <div class="cv-xlabels">
                <div class="cv-xlbl-spacer"></div>
                {xlabels}
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
            xlabels="\n".join(xlabels_html),
            last_year=last_year,
            last_prem=last_prem,
            last_cv=last_cv,
            summary_html=summary_html,
        )

    # Prepared-for line and date stamp
    today_str = date.today().strftime("%B %d, %Y")
    prepared_for_html = ""
    if client_name.strip():
        prepared_for_html = f'<div class="prepared-for">Prepared for <strong>{client_name.strip()}</strong></div>'
    date_html = f'<div class="date-stamp">{today_str}</div>'

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            margin-bottom: 40px;
            @bottom-center {{
                content: "Prepared by LIV Financial Group  |  {AGENT_LICENSE}  |  Page " counter(page) " of " counter(pages);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 8px;
                color: #6b7f8f;
            }}
        }}
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
            margin-bottom: 14px;
        }}
        .hero-logo-left {{
            flex: 0 0 auto;
        }}
        .logo {{
            height: 50px;
            width: auto;
            max-width: 160px;
            border-radius: 0;
            background: transparent;
            padding: 0;
            display: block;
        }}
        .agent-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-align: left;
        }}
        .agent-photo {{
            width: 80px;
            height: 80px;
            border-radius: 6px;
            border: 2px solid #ffffff;
            object-fit: cover;
            object-position: top center;
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
        .hero-bottom {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .hero-title-area {{
            flex: 1 1 auto;
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
        .prepared-for {{
            font-size: 14px;
            color: #ffffff;
            margin-top: 8px;
            font-weight: 400;
        }}
        .prepared-for strong {{
            font-weight: 700;
        }}
        .date-stamp {{
            font-size: 10px;
            color: rgba(255, 255, 255, 0.75);
            margin-top: 4px;
        }}
        .hero-nlg-right {{
            flex: 0 0 auto;
            margin-left: 20px;
        }}
        .logo-nlg {{
            height: 45px;
            width: auto;
        }}
        .content {{
            padding: 28px 32px 32px 32px;
        }}
        .section {{
            margin: 24px 0;
            page-break-before: always;
        }}
        .section.section-no-break {{
            page-break-before: avoid;
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
            display: table-header-group;
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
            grid-template-columns: auto auto auto auto;
            gap: 10px;
            margin: 14px 0 4px 0;
            justify-content: start;
        }}
        .info-item {{
            background: #ffffff;
            padding: 8px 14px;
            border: 1px solid #0e7fa6;
            border-radius: 6px;
            box-shadow: 0 1px 4px rgba(14, 127, 166, 0.12);
        }}
        .info-item strong {{
            display: block;
            color: #0e7fa6;
            margin-bottom: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid #d1e2ea;
            padding-bottom: 4px;
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
        .cv-chart-area {{
            display: flex;
            height: 200px;
        }}
        .cv-yaxis {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 200px;
            font-size: 9px;
            color: #476072;
            margin-right: 8px;
            flex-shrink: 0;
        }}
        .cv-ylabel {{
            text-align: right;
            min-width: 65px;
            white-space: nowrap;
        }}
        .cv-columns {{
            display: flex;
            align-items: flex-end;
            gap: 24px;
            height: 200px;
            flex: 1;
        }}
        .cv-col {{
            flex: 1;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 4px;
            height: 100%;
        }}
        .cv-bar-vertical {{
            position: relative;
            width: 22px;
            border-radius: 3px 3px 0 0;
        }}
        .cv-xlabels {{
            display: flex;
            margin-top: 6px;
        }}
        .cv-xlbl-spacer {{
            min-width: 73px;
            flex-shrink: 0;
        }}
        .cv-xlbl {{
            flex: 1;
            text-align: center;
            font-size: 10px;
            color: #476072;
        }}
        .cv-bar-vertical.premium {{
            background: #11b6c8;
        }}
        .cv-bar-vertical.cash {{
            background: #0e7fa6;
        }}
        .cv-value-label-vert {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            font-size: 7px;
            font-weight: 600;
            color: #123047;
            white-space: nowrap;
            margin-bottom: 2px;
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
            padding: 20px 0;
            margin: 24px 0;
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
                <span class="hero-logo-left">{logo_html}</span>
                {agent_info_html}
            </div>
            <div class="hero-bottom">
                <div class="hero-title-area">
                    <div class="hero-title">Policy Illustration Summary</div>
                    <div class="hero-subtitle">
                        Plan today, protect what matters most for a lifetime.
                    </div>
                    {prepared_for_html}
                    {date_html}
                </div>
                <span class="hero-nlg-right">{nlg_logo_html}</span>
            </div>
        </header>
        <main class="content">
            {html_body}
        </main>
    </div>
    <div class="page page-living">
        <div class="lb-heading-main">Living Benefits</div>
        <div class="lb-heading-sub">Benefits that can pay out while you're alive if you experience a qualifying event.</div>
        <div class="lb-banner">Coverage in case of a qualifying illness or injury</div>
        <div class="lb-grid">
            <div class="lb-card">
                <h3>Terminal Illness</h3>
                <p>Access a portion of your death benefit early if you are diagnosed with a qualifying terminal illness and your life expectancy is limited.</p>
                <p>This benefit can help cover medical expenses, pay off debt, or support your family during a difficult time.</p>
            </div>
            <div class="lb-card">
                <h3>Chronic Illness</h3>
                <p>If you're unable to perform basic activities of daily living or experience severe cognitive impairment, a portion of the benefit can be paid out while you are living.</p>
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


# ---------------------------------------------------------------------------
# Policy Submitted HTML template
# ---------------------------------------------------------------------------

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


def build_quote_comparison_html(
    client_name: str,
    client_age: str,
    carriers: list[dict],
    recommended_idx: int | None = None,
    logo_data_uri: str | None = None,
    agent_photo_data_uri: str | None = None,
) -> str:
    """Build a professional side-by-side quote comparison PDF.

    Each carrier dict has keys: carrier, product, monthly_premium,
    death_benefit, cash_value_10yr, rating.
    """
    today_str = date.today().strftime("%B %d, %Y")

    logo_html = (
        f'<img class="logo" src="{logo_data_uri}" alt="LIV Financial Logo" />'
        if logo_data_uri
        else ""
    )
    agent_photo_html = (
        f'<img class="agent-photo" src="{agent_photo_data_uri}" alt="{AGENT_NAME}" />'
        if agent_photo_data_uri
        else ""
    )

    # Build table rows for each carrier
    rows_html = ""
    for i, c in enumerate(carriers):
        rec_class = ' class="recommended"' if i == recommended_idx else ""
        rec_badge = ' <span class="rec-badge">RECOMMENDED</span>' if i == recommended_idx else ""
        rows_html += f"""
        <tr{rec_class}>
            <td class="carrier-name">{c.get('carrier', '—')}{rec_badge}</td>
            <td>{c.get('product', '—')}</td>
            <td class="num">{c.get('death_benefit', '—')}</td>
            <td class="num highlight">{c.get('monthly_premium', '—')}</td>
            <td class="num">{c.get('cash_value_10yr', '—')}</td>
            <td class="center">{c.get('rating', '—')}</td>
        </tr>"""

    # Build carrier detail cards
    cards_html = ""
    for i, c in enumerate(carriers):
        rec_border = "border-left: 4px solid #4CAF50;" if i == recommended_idx else ""
        rec_tag = '<div class="card-rec-tag">RECOMMENDED</div>' if i == recommended_idx else ""
        cards_html += f"""
        <div class="detail-card" style="{rec_border}">
            {rec_tag}
            <div class="detail-carrier">{c.get('carrier', '—')}</div>
            <div class="detail-product">{c.get('product', '—')}</div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Monthly Premium</div>
                    <div class="detail-value">{c.get('monthly_premium', '—')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Death Benefit</div>
                    <div class="detail-value">{c.get('death_benefit', '—')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">10-Year Cash Value</div>
                    <div class="detail-value">{c.get('cash_value_10yr', '—')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Rating</div>
                    <div class="detail-value">{c.get('rating', '—')}</div>
                </div>
            </div>
        </div>"""

    prepared_for_html = ""
    if client_name.strip():
        age_part = f", Age {client_age}" if client_age.strip() else ""
        prepared_for_html = f'<div class="prepared-for">Prepared for <strong>{client_name.strip()}{age_part}</strong></div>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
    @page {{
        margin-bottom: 40px;
        @bottom-center {{
            content: "Prepared by LIV Financial Group  |  {AGENT_LICENSE}  |  Page " counter(page) " of " counter(pages);
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
        margin-bottom: 14px;
    }}
    .logo {{
        height: 50px;
        width: auto;
        max-width: 160px;
        display: block;
    }}
    .agent-info {{
        display: flex;
        align-items: center;
        gap: 12px;
        text-align: left;
    }}
    .agent-photo {{
        width: 80px;
        height: 80px;
        border-radius: 6px;
        border: 2px solid #ffffff;
        object-fit: cover;
        object-position: top center;
        flex-shrink: 0;
    }}
    .agent-details {{ line-height: 1.3; }}
    .agent-name {{ font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 2px; }}
    .agent-detail {{ font-size: 10px; color: rgba(255,255,255,0.9); }}
    .hero-bottom {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .hero-title {{ font-size: 22px; font-weight: 500; margin-bottom: 4px; }}
    .hero-subtitle {{ font-size: 14px; opacity: 0.9; }}
    .prepared-for {{ font-size: 14px; color: #fff; margin-top: 6px; }}
    .prepared-for strong {{ font-weight: 700; }}
    .date-stamp {{ font-size: 10px; color: rgba(255,255,255,0.75); margin-top: 4px; }}
    .content {{ padding: 24px 32px 32px 32px; }}
    h2.section-title {{
        font-size: 18px;
        color: #0e7fa6;
        border-bottom: 2px solid #0e7fa6;
        padding-bottom: 6px;
        margin-bottom: 16px;
        font-weight: 600;
    }}
    /* Comparison table */
    table.compare {{
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 12px;
    }}
    table.compare thead {{
        background: #0e7fa6;
        color: #ffffff;
    }}
    table.compare th {{
        padding: 10px 8px;
        text-align: left;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    table.compare td {{
        padding: 10px 8px;
        border-bottom: 1px solid #e0edf3;
    }}
    table.compare td.num {{
        text-align: right;
        font-family: "Courier New", monospace;
        font-weight: 600;
    }}
    table.compare td.center {{ text-align: center; }}
    table.compare td.highlight {{
        color: #0e7fa6;
        font-size: 14px;
        font-weight: 700;
    }}
    table.compare td.carrier-name {{
        font-weight: 600;
        color: #123047;
    }}
    table.compare tr.recommended {{
        background: #eef9ee;
    }}
    .rec-badge {{
        display: inline-block;
        background: #4CAF50;
        color: #fff;
        font-size: 8px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 8px;
        vertical-align: middle;
        letter-spacing: 0.04em;
    }}
    /* Detail cards */
    .detail-cards {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin: 20px 0;
    }}
    .detail-card {{
        border: 1px solid #d1e2ea;
        border-radius: 8px;
        padding: 16px;
        background: #f9fcfe;
        position: relative;
    }}
    .card-rec-tag {{
        position: absolute;
        top: 10px;
        right: 10px;
        background: #4CAF50;
        color: #fff;
        font-size: 8px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 3px;
        letter-spacing: 0.04em;
    }}
    .detail-carrier {{
        font-size: 16px;
        font-weight: 700;
        color: #123047;
        margin-bottom: 2px;
    }}
    .detail-product {{
        font-size: 12px;
        color: #476072;
        margin-bottom: 12px;
    }}
    .detail-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }}
    .detail-label {{
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #0e7fa6;
        font-weight: 600;
        margin-bottom: 2px;
    }}
    .detail-value {{
        font-size: 14px;
        font-weight: 600;
        color: #123047;
    }}
    .disclaimer {{
        margin-top: 24px;
        font-size: 10px;
        color: #6b7f8f;
        line-height: 1.5;
    }}
    .next-steps {{
        margin-top: 20px;
        background: #e8f4f8;
        border-radius: 8px;
        padding: 16px 20px;
        border: 1px solid #d1e2ea;
    }}
    .next-steps h3 {{
        font-size: 14px;
        font-weight: 600;
        color: #0e7fa6;
        margin-bottom: 8px;
    }}
    .next-steps p {{
        font-size: 12px;
        color: #2c4a63;
        margin: 4px 0;
    }}
</style>
</head>
<body>
    <header class="hero">
        <div class="hero-top">
            <span>{logo_html}</span>
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
        </div>
        <div class="hero-bottom">
            <div>
                <div class="hero-title">Quote Comparison</div>
                <div class="hero-subtitle">Side-by-side carrier comparison to help you choose the best fit.</div>
                {prepared_for_html}
                <div class="date-stamp">{today_str}</div>
            </div>
        </div>
    </header>
    <div class="content">
        <h2 class="section-title">Carrier Comparison</h2>
        <table class="compare">
            <thead>
                <tr>
                    <th>Carrier</th>
                    <th>Product</th>
                    <th>Death Benefit</th>
                    <th>Monthly Premium</th>
                    <th>10-Yr Cash Value</th>
                    <th>Rating</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <h2 class="section-title">Detailed Breakdown</h2>
        <div class="detail-cards">
            {cards_html}
        </div>

        <div class="next-steps">
            <h3>Next Steps</h3>
            <p>1. Review the options above and consider which best fits your goals and budget.</p>
            <p>2. Ask me any questions about the differences between carriers or products.</p>
            <p>3. Once you decide, I will submit the application and guide you through every step.</p>
            <p>Contact me anytime: <strong>{AGENT_PHONE}</strong> or <strong>{AGENT_EMAIL}</strong></p>
        </div>

        <div class="disclaimer">
            This quote comparison is for illustration purposes only and is not an offer or contract.
            Premiums shown are estimates based on the information provided and may change based on
            underwriting. Cash value projections are non-guaranteed and based on current assumptions.
            Actual results may vary. Please review each carrier's full illustration for guaranteed values
            and complete policy details.
        </div>
    </div>
</body>
</html>"""


def build_business_card_html(card_data_uri: str) -> str:
    """Build Business Card HTML from the pre-composited business card image."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
    @page {{
        size: 10in 3.33in;
        margin: 0;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        width: 10in;
        height: 3.33in;
        overflow: hidden;
    }}
    .card-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}
</style>
</head>
<body>
    <img class="card-img" src="{card_data_uri}" alt="Business Card" />
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
