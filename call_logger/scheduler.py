"""Background scheduler for weekly Google Sheets export.

Imported by app.py at startup to register the Friday 6 PM job.
"""

from apscheduler.schedulers.background import BackgroundScheduler

import config
from sheets import export_week_to_sheets


def _weekly_export_job():
    """Run the weekly export, logging success or failure."""
    try:
        tab = export_week_to_sheets()
        print(f"[Scheduler] Weekly report exported to sheet tab: {tab}")
    except Exception as e:
        print(f"[Scheduler] Weekly export failed: {e}")


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
scheduler.start()
print(f"[Scheduler] Weekly export scheduled for {config.REPORT_DAY.upper()} "
      f"at {config.REPORT_HOUR}:{config.REPORT_MINUTE:02d}")
