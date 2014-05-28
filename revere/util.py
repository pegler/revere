from revere.db import db, Alert, Monitor, MonitorLog
from revere import app, scheduler
from sqlalchemy.sql import and_
import importlib
import datetime


def get_klass(klass):
    module_name, class_name = klass.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


# Alert utility functions
def send_alert(monitor, old_state, new_state, message, return_value):
    for alert_name, alert in app.alerts.items():
        alert_obj = Alert.query.filter_by(key=alert_name).first()
        if alert.enabled_in_config and new_state in alert_obj.get_alert_states():
            alert.trigger(monitor, old_state, new_state, message, return_value)


# Scheduler utility functions
def monitor_maintenance():
    try:
        for monitor in Monitor.query.all():
            now = datetime.datetime.utcnow()
            cutoff = now - datetime.timedelta(days=monitor.retain_days)
            MonitorLog.query.filter(and_(MonitorLog.monitor_id == monitor.id, MonitorLog.timestamp < cutoff)).delete(synchronize_session='fetch')
    except:
        db.session.rollback()
        raise
    else:
        db.session.commit()


def run_monitor(monitor_id):
    try:
        monitor = Monitor.query.get(monitor_id)
        monitor.run()
    except:
        db.session.rollback()
        raise
    else:
        db.session.commit()


def update_monitor_scheduler(monitor):
    # remove the old schedule
    job = app.monitor_jobs.get(monitor.id)
    if job:
        scheduler.unschedule_job(job)
        del app.monitor_jobs[monitor.id]

    if monitor.active:
        job = scheduler.add_cron_job(run_monitor,
                                     kwargs={'monitor_id': monitor.id},
                                     year=monitor.schedule_year,
                                     month=monitor.schedule_month,
                                     day=monitor.schedule_day,
                                     week=monitor.schedule_week,
                                     day_of_week=monitor.schedule_day_of_week,
                                     hour=monitor.schedule_hour,
                                     minute=monitor.schedule_minute,
                                     second=monitor.schedule_second)
        app.monitor_jobs[monitor.id] = job
