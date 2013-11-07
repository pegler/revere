from apscheduler.scheduler import Scheduler
from flask import Flask, render_template, request, url_for, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from sqlalchemy.sql import and_, not_
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.wsgi import WSGIContainer
from wtforms import validators
from wtforms.ext.sqlalchemy.orm import model_form
import argparse
import datetime
import importlib
import logging
import math
import os
import signal
import sqlalchemy.types as types
import sys

logger = logging.getLogger('revere')

root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.setLevel(logging.DEBUG)
root.addHandler(ch)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Revere - general purpose monitoring and alerting')
    subparsers = argparser.add_subparsers(help='sub-command help', dest='subparser_name')

    parser_run = subparsers.add_parser('run', help="run the server")
    parser_run.add_argument("-c", "--config", help="specify config file")
    parser_run.add_argument("-p", "--port", default='5000', help="port to run the server on")

    parser_init = subparsers.add_parser('init', help="initialize Revere - create a sqlite database and table")

    args = argparser.parse_args()

app = Flask('revere')
app.config['WTF_CSRF_ENABLED'] = False
app.config.from_pyfile('config.py')

scheduler = Scheduler()

DIRNAME = os.path.abspath(os.path.dirname(__file__))

### Models
if 'SQLALCHEMY_DATABASE_URI' not in app.config:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(DIRNAME, 'revere.db')

db = SQLAlchemy(app)


class ChoiceType(types.TypeDecorator):
    impl = types.Integer

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.iteritems() if v == value or k == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, index=True, unique=True)
    enabled = db.Column(db.Boolean, default=True)
    state_ok = db.Column(db.Boolean(), default=True)
    state_alarm = db.Column(db.Boolean(), default=True)
    state_error = db.Column(db.Boolean(), default=True)
    state_inactive = db.Column(db.Boolean(), default=False)

    @property
    def name(self):
        return alerts[self.key].name

    @property
    def description(self):
        return alerts[self.key].description

    def get_alert_states(self):
        if not self.enabled:
            return []

        states = []
        if self.state_ok:
            states.append('OK')
        if self.state_alarm:
            states.append('ALARM')
        if self.state_error:
            states.append('ERROR')
        if self.state_inactive:
            states.append('INACTIVE')

        return states

AlertForm = model_form(Alert, base_class=Form,
                       exclude=['id', 'key'])

MONITOR_OK = 0
MONITOR_ALARM = 1
MONITOR_ERROR = 2
MONITOR_INACTIVE = 3
MONITOR_STATES = (
    (MONITOR_OK, 'OK'),
    (MONITOR_ALARM, 'ALARM'),
    (MONITOR_ERROR, 'ERROR'),
    (MONITOR_INACTIVE, 'INACTIVE'),
)


class Monitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    task = db.Column(db.Text())
    active = db.Column(db.Boolean(), default=True)
    state = db.Column(ChoiceType(MONITOR_STATES))

    retain_days = db.Column(db.Integer(), default=28)

    schedule_year = db.Column(db.String(10), default="*")
    schedule_month = db.Column(db.String(10), default="*")
    schedule_day = db.Column(db.String(10), default="*")
    schedule_week = db.Column(db.String(10), default="*")
    schedule_day_of_week = db.Column(db.String(10), default="*")
    schedule_hour = db.Column(db.String(10), default="*")
    schedule_minute = db.Column(db.String(10), default="*")
    schedule_second = db.Column(db.String(10), default="0")

    def record_run(self, new_state, message, return_value):
        global db

        old_state = self.state

        state_changed = old_state != new_state
        if state_changed:
            send_alert(self, old_state, new_state, message, return_value)

        change = MonitorLog(monitor=self,
                            message=message,
                            return_value=return_value,
                            old_state=old_state,
                            new_state=new_state,
                            state_changed=state_changed,
                            timestamp=datetime.datetime.utcnow())

        self.state = new_state
        db.session.add(change)
        db.session.add(self)
        db.session.commit()

    def run(self):
        class MonitorFailure(Exception):
            pass

        retval = None
        message = None
        new_status = None

        try:
            exec(self.task)
        except MonitorFailure, e:
            message = unicode(e)
            new_status = 'ALARM'
        except Exception, e:
            message = unicode(e)
            new_status = 'ERROR'
        else:
            message = 'Monitor Passed'
            new_status = 'OK'

        self.record_run(new_status, message, retval)


class MonitorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitor.id'))
    monitor = db.relationship('Monitor',
        backref=db.backref('logs', lazy='dynamic'))
    message = db.Column(db.Text())
    return_value = db.Column(db.String(255))
    old_state = db.Column(ChoiceType(MONITOR_STATES))
    new_state = db.Column(ChoiceType(MONITOR_STATES))
    state_changed = db.Column(db.Boolean())
    timestamp = db.Column(db.DateTime(), index=True)

MonitorForm = model_form(Monitor, base_class=Form,
                        exclude=['id', 'state', 'logs'],
                        field_args={
                            'schedule_year': {
                                'validators': [validators.Length(min=4, max=50)]
                            },
                            'schedule_year': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_month': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_day': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_week': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_day_of_week': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_second': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_minute': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                            'schedule_second': {
                                'validators': [validators.Length(min=1, max=10)]
                            },
                        })


@app.route('/')
def monitor_list():
    monitors = Monitor.query.all()
    return render_template('monitor_list.html', monitors=monitors)


@app.route('/monitor/<monitor_id>')
def monitor_detail(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)
    return render_template('monitor_detail.html', monitor=monitor)


@app.route('/monitor/<monitor_id>/history')
def monitor_history(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)

    logs = monitor.logs.order_by('timestamp DESC')
    count = logs.count()
    per_page = 100
    last_page = math.ceil(count / float(per_page))
    page = 1

    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1

    if page > last_page:
        page = last_page
    if page < 1:
        page = 1
    page = int(page)
    page_logs = logs.limit(per_page).offset((page - 1) * per_page)

    return render_template('monitor_history.html',
                           monitor=monitor,
                           page_logs=page_logs,
                           count=count,
                           per_page=per_page,
                           last_page=last_page,
                           page=page)


@app.route('/monitor/<monitor_id>/edit', methods=['GET', 'POST'])
def monitor_edit(monitor_id):
    monitor = Monitor.query.get_or_404(monitor_id)

    form = MonitorForm(request.form, monitor)
    if form.validate_on_submit():
        form.populate_obj(monitor)
        db.session.add(monitor)
        db.session.commit()
        monitor.record_run('INACTIVE', 'Monitor edited', None)
        update_monitor_scheduler(monitor)
        return redirect(url_for('monitor_detail', monitor_id=monitor.id))
    return render_template('monitor_edit.html', form=form, sources=sources, monitor=monitor, create=False)


@app.route('/create', methods=['GET', 'POST'])
def create():
    form = MonitorForm(request.form)
    if request.method == 'POST' and form.validate():
        new_monitor = Monitor(state='INACTIVE')
        form.populate_obj(new_monitor)
        db.session.add(new_monitor)
        db.session.commit()
        update_monitor_scheduler(new_monitor)
        return redirect(url_for('monitor_detail', monitor_id=new_monitor.id))
    return render_template('monitor_edit.html', form=form, sources=sources, create=True)


@app.route('/alerts')
def alert_list():
    alerts = Alert.query.all()
    return render_template('alert_list.html', alerts=alerts)


@app.route('/alert/<alert_id>/edit', methods=['GET', 'POST'])
def alert_edit(alert_id):
    alert = Alert.query.get_or_404(alert_id)

    form = AlertForm(request.form, alert)
    if form.validate_on_submit():
        form.populate_obj(alert)
        db.session.add(alert)
        db.session.commit()
        return redirect(url_for('alert_list'))
    return render_template('alert_edit.html', form=form, alert=alert)


def get_klass(klass):
    module_name, class_name = klass.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

### Define our data structures
sources = {}
alerts = {}
monitor_jobs = {}


### Alert utility functions
def send_alert(monitor, old_state, new_state, message, return_value):
    for alert_name, alert in alerts.items():
        alert_obj = Alert.query.filter_by(key=alert_name).first()
        if new_state in alert_obj.get_alert_states():
            alert.trigger(monitor, old_state, new_state, message, return_value)

## Scheduler utility functions


def monitor_maintenance():
    for monitor in Monitor.query.all():
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(days=monitor.retain_days)
        MonitorLog.query.filter(and_(MonitorLog.monitor_id == monitor.id, MonitorLog.timestamp < cutoff)).delete()


def run_monitor(monitor_id):
    monitor = Monitor.query.get(monitor_id)
    monitor.run()


def update_monitor_scheduler(monitor):
    global scheduler, monitor_jobs
    #remove the old schedule
    job = monitor_jobs.get(monitor.id)
    if job:
        scheduler.unschedule_job(job)
        del monitor_jobs[monitor.id]

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
        monitor_jobs[monitor.id] = job

## Allow clean exiting

is_closing = False


def signal_handler(signum, frame):
    global is_closing
    logger.info('exiting...')
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        logger.info('Stopping ')
        IOLoop.instance().stop()
        scheduler.shutdown()
        logger.info('exit success')


### Initialization function - call after we initialize Flask and the DB
def initialize_revere():
    global sources, alerts

    ### Initialize the sources
    for source_name, source_details in app.config.get('REVERE_SOURCES', {}).items():
        sources[source_name] = get_klass(source_details['type'])(description=source_details.get('description'),
                                                                 config=source_details['config'])

    ### Initialize the alerts
    for alert_name, alert_details in app.config.get('REVERE_ALERTS', {}).items():
        alerts[alert_name] = get_klass(alert_details['type'])(description=alert_details.get('description'),
                                                              config=alert_details['config'])
        alert = Alert.query.filter_by(key=alert_name).first()
        if not alert:
            alert = Alert(key=alert_name)
            db.session.add(alert)
    db.session.commit()

    Alert.query.filter(not_(Alert.key.in_(alerts.keys()))).delete(synchronize_session='fetch')

    # Run the maintenance routine hourly
    scheduler.add_cron_job(monitor_maintenance, year="*", month="*", day="*", hour="*", minute="0")


if __name__ == '__main__':
    if args.subparser_name == 'init':
        db.create_all()
        sys.exit(0)

    if args.subparser_name == 'run':
        signal.signal(signal.SIGINT, signal_handler)
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(args.port)
        PeriodicCallback(try_exit, 100).start()
        logger.info('Scheduling monitors')
        for monitor in Monitor.query.filter_by(active=True):
            update_monitor_scheduler(monitor)
        logger.info('Scheduler starting')
        scheduler.start()
        logger.info('Scheduler started')
        logger.info('Initializing Revere')
        initialize_revere()
        logger.info('Initialized Revere')
        logger.info('Tornado (webserver) starting')
        logger.info('Revere Server running on port %s' % args.port)
        IOLoop.instance().start()
        sys.exit(0)
