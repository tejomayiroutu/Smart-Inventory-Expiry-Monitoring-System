import atexit
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from services.expiry_alerts import send_daily_expiry_digests

scheduler = BackgroundScheduler(daemon=True)
_shutdown_registered = False


def _should_start_scheduler(app):
    if not app.config.get("SCHEDULER_ENABLED", True):
        return False
    # With debug=True, Werkzeug runs a parent reloader + a child worker. Starting the
    # scheduler in the parent would duplicate jobs; only start in the real worker.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return False
    return True


def init_scheduler(app):
    global _shutdown_registered

    if not _should_start_scheduler(app):
        return

    job_id = "daily_expiry_digest"

    def run_job():
        send_daily_expiry_digests(app)

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    hour = int(app.config.get("SCHEDULER_HOUR", 8))
    minute = int(app.config.get("SCHEDULER_MINUTE", 0))
    scheduler.add_job(
        run_job,
        CronTrigger(hour=hour, minute=minute),
        id=job_id,
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
        if not _shutdown_registered:
            atexit.register(lambda: scheduler.shutdown(wait=False))
            _shutdown_registered = True
