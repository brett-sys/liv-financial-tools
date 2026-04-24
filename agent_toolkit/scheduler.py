"""Background scheduler for weekly export and daily push reminders."""

from apscheduler.schedulers.background import BackgroundScheduler

import config
from sheets import export_week_to_sheets
from push import send_follow_up_reminders


def _weekly_export_job():
    try:
        tab = export_week_to_sheets()
        print(f"[Scheduler] Weekly report exported: {tab}")
    except Exception as e:
        print(f"[Scheduler] Weekly export failed: {e}")


def _daily_push_reminders():
    try:
        send_follow_up_reminders()
        print("[Scheduler] Follow-up push reminders sent.")
    except Exception as e:
        print(f"[Scheduler] Push reminders failed: {e}")


def _daily_email_reminders():
    """Send morning follow-up reminder emails to each agent."""
    if not config.REMINDER_ENABLED:
        return
    if not config.SMTP_EMAIL or not config.SMTP_PASSWORD:
        print("[Scheduler] Email reminders skipped: SMTP not configured")
        return

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from models.calls import get_stats

    for agent in config.AGENTS:
        name = agent["name"]
        email = agent.get("email", "")
        if not email:
            continue

        stats = get_stats(agent_name=name)
        due = stats.get("due_today", [])
        if not due:
            continue

        items_html = ""
        for d in due:
            phone = d.get('phone_number', '')
            notes = d.get('notes', '')
            phone_str = f" — {phone}" if phone else ""
            notes_str = f"<br><small style='color:#666;'>{notes[:100]}</small>" if notes else ""
            items_html += f"<li><strong>{d.get('contact_name', 'Unknown')}</strong>{phone_str}{notes_str}</li>"

        body = f"""
        <div style="font-family: -apple-system, sans-serif; max-width: 500px;">
            <h2 style="color: #0e7fa6;">Good morning, {name}!</h2>
            <p>You have <strong>{len(due)}</strong> follow-up{'s' if len(due) != 1 else ''} today:</p>
            <ul style="line-height: 1.8;">{items_html}</ul>
            <p style="margin-top: 16px;">
                <a href="https://tools.livfinancialgroup.com/dashboard"
                   style="background:#0e7fa6;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
                    Open Dashboard
                </a>
            </p>
            <p style="font-size:12px;color:#999;margin-top:20px;">— LIFI Agent Toolkit</p>
        </div>
        """

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"\U0001f4de {len(due)} follow-up{'s' if len(due) != 1 else ''} today \u2014 LIFI"
            msg["From"] = config.SMTP_EMAIL
            msg["To"] = email
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
                server.send_message(msg)
            print(f"[Scheduler] Reminder email sent to {name} ({email})")
        except Exception as e:
            print(f"[Scheduler] Reminder email to {name} failed: {e}")


scheduler = BackgroundScheduler(daemon=True)

scheduler.add_job(
    _weekly_export_job,
    trigger="cron",
    day_of_week=config.REPORT_DAY,
    hour=config.REPORT_HOUR,
    minute=config.REPORT_MINUTE,
    id="weekly_sheets_export",
    replace_existing=True,
)

scheduler.add_job(
    _daily_push_reminders,
    trigger="cron",
    hour=8,
    minute=30,
    id="daily_push_reminders",
    replace_existing=True,
)

if config.REMINDER_ENABLED:
    scheduler.add_job(
        _daily_email_reminders,
        trigger="cron",
        hour=config.REMINDER_HOUR,
        minute=config.REMINDER_MINUTE,
        id="daily_email_reminders",
        replace_existing=True,
    )
    print(f"[Scheduler] Daily email reminders: {config.REMINDER_HOUR}:{config.REMINDER_MINUTE:02d} AM")

scheduler.start()
print(f"[Scheduler] Weekly export: {config.REPORT_DAY.upper()} at {config.REPORT_HOUR}:{config.REPORT_MINUTE:02d}")
print("[Scheduler] Daily push reminders: 8:30 AM")
