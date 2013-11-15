from revere import db, app
import datetime
import sqlalchemy.types as types


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
        return app.alerts[self.key].name

    @property
    def description(self):
        return app.alerts[self.key].description

    @property
    def enabled_in_config(self):
        return app.alerts[self.key].enabled_in_config

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
    last_run_timestamp = db.Column(db.DateTime())

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
            from revere.util import send_alert
            send_alert(self, old_state, new_state, message, return_value)

        timestamp = datetime.datetime.utcnow()

        change = MonitorLog(monitor=self,
                            message=message,
                            return_value=return_value,
                            old_state=old_state,
                            new_state=new_state,
                            state_changed=state_changed,
                            timestamp=timestamp)

        self.state = new_state
        self.last_run_timestamp = timestamp
        db.session.add(change)
        db.session.add(self)
        db.session.commit()

    def run(self):
        class MonitorFailure(Exception):
            pass

        return_value = None
        message = None
        new_status = None
        sources = app.sources  # noqa

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

        if return_value is not None and not isinstance(return_value, (int, float, basestring)):
            return_value = 'Invalid return_value'

        self.record_run(new_status, message, return_value)


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
