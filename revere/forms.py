from flask.ext.wtf import Form
from wtforms import validators
from wtforms.ext.sqlalchemy.orm import model_form
from revere.db import Alert, Monitor

AlertForm = model_form(Alert,
                       base_class=Form,
                       exclude=['id', 'key'])

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
