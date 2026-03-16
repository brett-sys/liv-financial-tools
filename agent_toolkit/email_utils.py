"""Email utility – send illustration PDFs to clients via SMTP."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import config


class EmailError(Exception):
    pass


def _check_config():
    if not config.SMTP_EMAIL:
        return "SMTP_EMAIL not configured in .env"
    if not config.SMTP_PASSWORD:
        return "SMTP_PASSWORD not configured in .env"
    return None


def send_illustration_email(client_name, client_email, pdf_bytes, filename):
    """Send a branded illustration PDF to a client.

    Returns dict with 'success' and 'message' keys.
    """
    err = _check_config()
    if err:
        raise EmailError(err)

    msg = MIMEMultipart()
    msg["From"] = f"{config.AGENT_NAME} <{config.SMTP_EMAIL}>"
    msg["To"] = client_email
    msg["Subject"] = f"Your IUL Illustration – {client_name}"

    body = (
        f"Hi {client_name.split()[0]},\n\n"
        f"Thank you for taking the time to explore your financial options. "
        f"Attached is your personalized IUL illustration from LIV Financial Group.\n\n"
        f"This document breaks down your policy values, projected cash value growth, "
        f"and coverage details. Please review it at your convenience.\n\n"
        f"If you have any questions or would like to discuss next steps, "
        f"don't hesitate to reach out.\n\n"
        f"Best regards,\n"
        f"{config.AGENT_NAME}\n"
        f"{config.AGENT_TITLE}\n"
        f"LIV Financial Group\n"
        f"{config.AGENT_PHONE}\n"
        f"{config.AGENT_EMAIL_DISPLAY}\n"
        f"{config.AGENT_WEBSITE}"
    )
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise EmailError(
            "SMTP authentication failed. Check SMTP_EMAIL and SMTP_PASSWORD in .env. "
            "For Gmail, use an App Password (not your regular password)."
        )
    except smtplib.SMTPException as e:
        raise EmailError(f"SMTP error: {e}")
    except OSError as e:
        raise EmailError(f"Could not connect to mail server: {e}")
