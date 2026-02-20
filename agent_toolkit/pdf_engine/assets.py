"""Asset loaders for PDF engine – loads images as base64 data URIs."""

import base64
import logging
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

log = logging.getLogger(__name__)

PACKAGE_DIR = config.PDF_ENGINE_DIR


def _load_image(relative_path):
    try:
        img_path = PACKAGE_DIR / relative_path
        if not img_path.exists():
            log.warning("Image not found: %s", img_path)
            return None
        data = img_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        suffix = img_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        log.warning("Failed to load image: %s", relative_path, exc_info=True)
        return None


def load_logo_data_uri():
    return _load_image(config.LOGO_FILENAME)


def load_nlg_logo_data_uri():
    return _load_image(config.NLG_LOGO_FILENAME)


def load_agent_photo_data_uri():
    return _load_image(config.AGENT_PHOTO_FILENAME)


def load_business_card_data_uri():
    return _load_image(config.BUSINESS_CARD_FILENAME)
