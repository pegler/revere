from apscheduler.scheduler import Scheduler
from flask import Flask, request
from flask.ext.googleauth import GoogleFederated
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import not_
import os
from werkzeug.contrib.fixers import ProxyFix

app = Flask('revere')
app.config['WTF_CSRF_ENABLED'] = False
app.config.from_pyfile(os.environ.get('REVERE_CONFIG_FILE', 'config.py'))

database_path = app.config.get('DATABASE_PATH', 'revere.db')
if database_path[0] != '/':
    database_path = os.path.join(os.getcwd(), database_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path

scheduler = Scheduler()

db = SQLAlchemy(app)

google_apps_domain = app.config.get('GOOGLE_APPS_DOMAIN', None)
if google_apps_domain:
    auth = GoogleFederated(google_apps_domain, app)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = app.config.get('SECRET_KEY') or app.config.get('COOKIE_SECRET')

    def _force_auth_on_every_request():

        @auth.required
        def _should_auth():
            return None

        if request.path.startswith('/login'):
            return None

        return _should_auth()

    app.before_request(_force_auth_on_every_request)

# Define our data structures
app.sources = {}
app.alerts = {}
app.monitor_jobs = {}


def initialize(app):
    # Initialize the sources
    for source_name, source_details in app.config.get('REVERE_SOURCES', {}).items():
        if source_details.get('enabled') is False:
            continue
        app.sources[source_name] = get_klass(source_details['type'])(description=source_details.get('description'),
                                                                 config=source_details['config'])

    # Initialize the alerts
    for alert_name, alert_details in app.config.get('REVERE_ALERTS', {}).items():
        app.alerts[alert_name] = get_klass(alert_details['type'])(description=alert_details.get('description'),
                                                                  config=alert_details['config'],
                                                                  enabled_in_config=alert_details.get('enabled', True))
        alert = Alert.query.filter_by(key=alert_name).first()
        if not alert:
            alert = Alert(key=alert_name)
            db.session.add(alert)

    Alert.query.filter(not_(Alert.key.in_(app.alerts.keys()))).delete(synchronize_session='fetch')
    db.session.commit()

    # Run the maintenance routine hourly
    scheduler.add_cron_job(monitor_maintenance, year="*", month="*", day="*", hour="*", minute="0")

    for monitor in Monitor.query.filter_by(active=True):
        update_monitor_scheduler(monitor)

    scheduler.start()

if True:  # Keep this at the bottom of the file
    from revere.db import db, Alert, Monitor
    from revere.util import get_klass, monitor_maintenance, update_monitor_scheduler
    import revere.views  # noqa
