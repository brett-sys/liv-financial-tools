"""Asset loaders — load images as base64 data URIs for embedding in HTML."""

import base64
import logging
from pathlib import Path

from .config import PACKAGE_DIR, LOGO_FILENAME, NLG_LOGO_FILENAME, AGENT_PHOTO_FILENAME, BUSINESS_CARD_FILENAME

log = logging.getLogger(__name__)


def load_logo_data_uri() -> str | None:
    """Load a local PNG logo and return a data: URI.

    Put the logo file next to this script (same folder) using the exact name in
    LOGO_FILENAME, and it will be embedded into the PDF header.
    """
    try:
        logo_path = PACKAGE_DIR / LOGO_FILENAME
        if not logo_path.exists():
            log.warning("Logo file not found: %s", logo_path)
            return None
        data = logo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        log.warning("Failed to load logo from %s", LOGO_FILENAME, exc_info=True)
        return None


def load_nlg_logo_data_uri() -> str | None:
    """Load National Life Group PNG logo; return data URI or None if missing."""
    try:
        logo_path = PACKAGE_DIR / NLG_LOGO_FILENAME
        if not logo_path.exists():
            log.warning("NLG logo file not found: %s", logo_path)
            return None
        data = logo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        log.warning("Failed to load NLG logo from %s", NLG_LOGO_FILENAME, exc_info=True)
        return None


def load_agent_photo_data_uri() -> str | None:
    """Load agent headshot image and return a data: URI, or None if missing."""
    try:
        photo_path = PACKAGE_DIR / AGENT_PHOTO_FILENAME
        if not photo_path.exists():
            log.warning("Agent photo not found: %s", photo_path)
            return None
        data = photo_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        suffix = photo_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        log.warning("Failed to load agent photo from %s", AGENT_PHOTO_FILENAME, exc_info=True)
        return None


def load_business_card_data_uri() -> str | None:
    """Load business card image and return a data: URI, or None if missing."""
    try:
        card_path = PACKAGE_DIR / BUSINESS_CARD_FILENAME
        if not card_path.exists():
            log.warning("Business card image not found: %s", card_path)
            return None
        data = card_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        log.warning("Failed to load business card from %s", BUSINESS_CARD_FILENAME, exc_info=True)
        return None
