"""Render the North American rollover-funding reference as a LIV-branded PDF.

Uses the pre-installed Chromium (via Playwright) to render an HTML document
styled with the LIV hero header — the same look as the other LIV packets —
into docs/north-american-forms/LIV-North-American-Rollover-Funding.pdf.
"""

import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "pdf_generator" / "assets" / "234_transparent.png"
PHOTO = ROOT / "pdf_generator" / "assets" / "agent_headshot.png"
OUT = ROOT / "docs" / "north-american-forms" / "LIV-North-American-Rollover-Funding.pdf"

AGENT_NAME = "Brett Dunham"
AGENT_TITLE = "Agency Owner"
AGENT_PHONE = "(714) 335-1412"
AGENT_EMAIL = "brett@fflliv.com"
AGENT_LICENSE = "License #21114292"
AGENT_WEBSITE = "www.livfinancialgroup.com"


def data_uri(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


logo_uri = data_uri(LOGO)
photo_uri = data_uri(PHOTO)

HTML = f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #123047; line-height: 1.55; font-size: 12.5px;
  }}
  .hero {{ background: #0e7fa6; color: #fff; padding: 20px 40px 22px 40px; }}
  .hero-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
  .logo {{ height: 58px; width: auto; max-width: 200px; display: block; }}
  .agent-info {{ display: flex; align-items: center; gap: 12px; }}
  .agent-photo {{ width: 74px; height: 74px; border-radius: 6px; border: 2px solid #fff;
                  object-fit: cover; object-position: top center; }}
  .agent-details {{ line-height: 1.3; text-align: right; }}
  .agent-name {{ font-size: 13px; font-weight: 700; }}
  .agent-detail {{ font-size: 10px; color: rgba(255,255,255,0.9); }}
  .hero-title {{ font-size: 23px; font-weight: 600; margin-bottom: 4px; }}
  .hero-subtitle {{ font-size: 13px; opacity: 0.92; }}
  .content {{ padding: 26px 40px 40px 40px; }}
  h2 {{ font-size: 16px; color: #0e7fa6; border-bottom: 2px solid #0e7fa6;
        padding-bottom: 5px; margin: 22px 0 12px 0; }}
  h2:first-of-type {{ margin-top: 4px; }}
  p {{ margin-bottom: 10px; }}
  ul {{ margin: 0 0 12px 20px; }}
  li {{ margin-bottom: 6px; }}
  .callout {{ background: #f0f7fa; border-left: 4px solid #0e7fa6; padding: 12px 16px;
              margin: 12px 0; border-radius: 4px; }}
  .lead {{ font-size: 13px; font-weight: 600; color: #123047; }}
  a {{ color: #0e7fa6; word-break: break-all; }}
  .footer-note {{ margin-top: 26px; padding-top: 12px; border-top: 1px solid #d7e2ea;
                  font-size: 9.5px; color: #6b7f8f; }}
</style></head>
<body>
  <header class="hero">
    <div class="hero-top">
      <img class="logo" src="{logo_uri}" alt="LIV Financial Group" />
      <div class="agent-info">
        <img class="agent-photo" src="{photo_uri}" alt="{AGENT_NAME}" />
        <div class="agent-details">
          <div class="agent-name">{AGENT_NAME}</div>
          <div class="agent-detail">{AGENT_TITLE}</div>
          <div class="agent-detail">{AGENT_PHONE}</div>
          <div class="agent-detail">{AGENT_EMAIL}</div>
          <div class="agent-detail">{AGENT_LICENSE}</div>
        </div>
      </div>
    </div>
    <div class="hero-title">How North American Rollover &amp; Transfer Funds Are Delivered</div>
    <div class="hero-subtitle">Why the money usually arrives by check &mdash; and why that's normal</div>
  </header>

  <div class="content">
    <p class="lead">When a client moves qualified money (an IRA or 401(k) rollover) or does a
    1035 exchange into a North American annuity, the current institution most commonly sends
    the funds as a physical check &mdash; not a wire or ACH.</p>
    <p>The check is mailed to North American and clears there before the new contract is funded.
    A check in the mail does <strong>not</strong> mean anything went wrong; it is the standard
    way most institutions release transferred funds.</p>

    <h2>Why it comes by check</h2>
    <p>Most banks, custodians, and insurance carriers still fund outgoing transfers and 1035
    exchanges by paper check. Wire and ACH are available at some institutions but are the
    exception, not the rule. Check is the lowest-common-denominator method that virtually every
    institution supports &mdash; which is why &ldquo;it will come by check&rdquo; is the safe
    answer to give a client.</p>

    <h2>The check is payable to the carrier &mdash; not the client</h2>
    <p>This is the part that protects the client's tax treatment:</p>
    <ul>
      <li>On a 1035 exchange or a direct/trustee-to-trustee rollover, the check is made payable
      to <strong>North American Company FBO [Client Name]</strong> (&ldquo;FBO&rdquo; = for the
      benefit of) and mailed to North American.</li>
      <li>The client should <strong>never</strong> receive a check made payable to them
      personally for a 1035 exchange or direct rollover. If they do, the IRS can treat it as a
      taxable surrender or distribution rather than a tax-free transfer.</li>
      <li>So &ldquo;the money comes by check&rdquo; is true &mdash; but it's a
      <strong>carrier-payable check</strong>, which keeps the transfer direct and tax-free.</li>
    </ul>

    <h2>Typical timeline</h2>
    <p>A check-based transfer generally takes <strong>about 2&ndash;6 weeks</strong> end to end
    (current institution processing + mail time + North American posting the funds).</p>

    <div class="callout">
      <strong>Source / authoritative form:</strong> The industry-standard document for this is
      the <strong>1035 Exchange / Rollover / Transfer form (ACORD 951)</strong>, which North
      American and most carriers use. It directs the surrendering institution to send the funds
      to the receiving carrier on the client's behalf &mdash; i.e. the by-check,
      payable-to-carrier process described above. For North American's own branded copy, pull the
      current version from the North American agent portal &rarr; Forms library.
    </div>

    <div class="footer-note">
      Prepared by LIV Financial Group &nbsp;|&nbsp; {AGENT_LICENSE} &nbsp;|&nbsp; {AGENT_WEBSITE}.
      This is an internal LIV Financial explainer for client conversations, not an official North
      American Company publication. For carrier-issued documents, use North American's forms or
      contact North American directly.
    </div>
  </div>
</body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page()
        page.set_content(HTML, wait_until="networkidle")
        page.pdf(path=str(OUT), format="Letter",
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                 print_background=True)
        browser.close()
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
