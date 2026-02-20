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

scheduler.start()
print(f"[Scheduler] Weekly export: {config.REPORT_DAY.upper()} at {config.REPORT_HOUR}:{config.REPORT_MINUTE:02d}")
print("[Scheduler] Daily push reminders: 8:30 AM")
