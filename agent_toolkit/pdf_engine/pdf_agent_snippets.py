"""Shared agent HTML for PDF headers and footers (no photo, license, email, or phone)."""


def pdf_agent_header_html(ai: dict) -> str:
    """Hero block: name, title, website."""
    return f"""
            <div class="agent-info">
                <div class="agent-details">
                    <div class="agent-name">{ai["name"]}</div>
                    <div class="agent-detail">{ai["title"]}</div>
                    <div class="agent-detail">{ai["website"]}</div>
                </div>
            </div>"""


def pdf_footer_contact_bullets(ai: dict) -> str:
    """Name and optional website — bullet-separated for disclaimers."""
    parts: list[str] = []
    name = (ai.get("name") or "").strip()
    if name:
        parts.append(name)
    site = (ai.get("website") or "").strip()
    if site:
        parts.append(site)
    return " &bull; ".join(parts)


def pdf_next_steps_contact_line(ai: dict) -> str:
    """Next-steps CTA without phone or email."""
    site = (ai.get("website") or "").strip()
    if site:
        return f'<p>Visit <strong>{site}</strong> anytime.</p>'
    return "<p>Contact me anytime.</p>"
