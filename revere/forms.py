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
                'validators': [validators.Length(min=1, max=50)]
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
        }