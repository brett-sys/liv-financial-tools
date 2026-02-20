"""Calendar integration – Google Calendar URLs and .ics file generation."""

from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
import uuid

import config


def _format_gcal_date(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


def _build_event_data(contact_name, phone_number, follow_up_date, notes=""):
    title = f"Follow-up: {contact_name}"
    if phone_number:
        title += f" ({phone_number})"

    description = f"Follow-up call with {contact_name}\n"
    if phone_number:
        description += f"Phone: {phone_number}\n"
    if notes:
        description += f"\nNotes from last call:\n{notes}"

    start_dt = datetime.strptime(follow_up_date, "%Y-%m-%d").replace(hour=9, minute=0)
    end_dt = start_dt + timedelta(minutes=30)

    return title, description, start_dt, end_dt


def _google_calendar_url(title, description, start_dt, end_dt, guest_email=""):
    url = (
        "https://calendar.google.com/calendar/event?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={_format_gcal_date(start_dt)}/{_format_gcal_date(end_dt)}"
        f"&details={quote(description)}"
        f"&ctz=America/Chicago"
    )
    if guest_email:
        url += f"&add={quote(guest_email)}"
    return url


def _ics_download_url(contact_name, phone_number, follow_up_date, notes):
    params = urlencode({
        "contact": contact_name,
        "phone": phone_number,
        "date": follow_up_date,
        "notes": notes,
    })
    return f"/calendar.ics?{params}"


def generate_ics(contact_name, phone_number, follow_up_date, notes=""):
    title, description, start_dt, end_dt = _build_event_data(
        contact_name, phone_number, follow_up_date, notes
    )

    uid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    start = start_dt.strftime("%Y%m%dT%H%M%S")
    end = end_dt.strftime("%Y%m%dT%H%M%S")

    desc_escaped = description.replace("\n", "\\n").replace(",", "\\,")
    title_escaped = title.replace(",", "\\,")

    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//LIFI Agent Toolkit//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART;TZID=America/Chicago:{start}\r\n"
        f"DTEND;TZID=America/Chicago:{end}\r\n"
        f"SUMMARY:{title_escaped}\r\n"
        f"DESCRIPTION:{desc_escaped}\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT30M\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Follow-up reminder\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def get_calendar_urls(agent_name, contact_name, phone_number,
                      follow_up_date, notes=""):
    title, description, start_dt, end_dt = _build_event_data(
        contact_name, phone_number, follow_up_date, notes
    )
    agent_email = config.AGENT_EMAILS.get(agent_name, "")

    return {
        "gcal": _google_calendar_url(title, description, start_dt, end_dt,
                                     guest_email=agent_email),
        "ics": _ics_download_url(contact_name, phone_number, follow_up_date, notes),
        "agent": agent_name,
    }
