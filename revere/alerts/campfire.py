from revere.alerts.base import BaseRevereAlert
import requests
import json


class CampfireAlert(BaseRevereAlert):
    name = 'Campfire'

    def __init__(self, description, config):
        super(CampfireAlert, self).__init__(description, config)

        required_params = ['api_token', 'room_id', 'subdomain']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('Campfire Alert Improperly Configured: missing parameter: %s' % param)
        self.config = config

    def trigger(self, monitor, old_state, new_state, message, return_value):
        message_vars = {
            'monitor_name': monitor.name,
            'old_state': old_state,
            'new_state': new_state,
            'message': message,
            'return_value': return_value,
        }
        message = json.dumps({
            'message': {
                'body': '[Revere Alarm]\nMonitor: %(monitor_name)s\nState Change: %(old_state)s -> %(new_state)s\nMessage: %(message)s\nReturn Value: %(return_value)s' % message_vars,
                'type': 'PasteMessage'
            }
        })

        headers = {'Content-Type': 'application/json'}
        auth = (self.config['api_token'], 'X')

        requests.post('https://{subdomain}.campfirenow.com/room/{room_id}/speak.json'.format(**self.config),
                      data=message,
                      headers=headers,
                      auth=auth)
