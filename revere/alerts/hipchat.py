from revere.alerts.base import BaseRevereAlert
import requests
import json


class HipChatAlert(BaseRevereAlert):
    name = 'HipChat'

    def __init__(self, description, config, enabled_in_config=True):
        super(HipChatAlert, self).__init__(description, config, enabled_in_config)

        required_params = ['auth_token', 'room_name']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('HipChat Alert Improperly Configured: missing parameter: %s' % param)
        self.config = config

    def trigger(self, monitor, old_state, new_state, message, return_value):
        message_vars = {
            'monitor_name': monitor.name,
            'old_state': old_state,
            'new_state': new_state,
            'message': message,
            'return_value': return_value,
        }
        
        color = 'green' if new_state == 'OK' else 'red'
        
        params = {
            'room_id': self.config['room_name'],
            'from': self.config.get('from_name', 'Revere'),
            'message': '[Revere Alarm]\nMonitor: %(monitor_name)s\nState Change: %(old_state)s -> %(new_state)s\nMessage: %(message)s\nReturn Value: %(return_value)s' % message_vars,
            'message_format': 'text',
            'notify': '1',
            'color': color,
        }

        headers = {'Content-Type': 'application/json'}

        response = requests.post('https://api.hipchat.com/v1/rooms/message?auth_token=%s' % self.config['auth_token'],
                      params=params,
                      headers=headers)
