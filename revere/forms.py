from flask.ext.wtf import Form
from wtforms import validators
from wtforms_alchemy import model_form_factory
from revere.db import Alert, Monitor


ModelForm = model_form_factory(Form)


class AlertForm(ModelForm):
    class Meta:
        model = Alert
        exclude = ['key']


class MonitorForm(ModelForm):
    class Meta:
        model = Monitor
        exclude = ['state']
        field_args = {
            'schedule_year': {
                'default': '*',
                'validators': [validators.Length(min=1, max=50)]
            },
            'schedule_month': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_day': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_week': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_day_of_week': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_second': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_minute': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
            'schedule_second': {
                'default': '*',
                'validators': [validators.Length(min=1, max=10)]
            },
        }
