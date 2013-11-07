from revere.alerts.base import BaseRevereAlert
import base64
import hashlib
import hmac
import json
import requests
import urllib2
import datetime


class SNSAlert(BaseRevereAlert):
    name = 'Amazon SNS'

    def __init__(self, description, config):
        super(SNSAlert, self).__init__(description, config)

        required_params = ['topic_arn', 'access_key_id', 'secret_key']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('AWS SNS Alert Improperly Configured: missing parameter: %s' % param)
        self.config = config

    def trigger(self, monitor, old_state, new_state, message, return_value):
        amazon_host = 'sns.%s.amazonaws.com' % self.config.get('region', 'us-east-1')
        
        message_vars = {
            'monitor_name': monitor.name,
            'old_state': old_state,
            'new_state': new_state,
            'message': message,
            'return_value': return_value,
        }
        
        subject = '[Revere Alarm] %(new_state)s %(monitor_name)s' % message_vars
        message = json.dumps({
            'default': 'Monitor: %(monitor_name)s\nState Change: %(old_state)s -> %(new_state)s\nMessage: %(message)s\nReturn Value: %(return_value)s' % message_vars,
            'sms': '[Revere] %(new_state)s %(monitor_name)s' % message_vars,
        })
        
        params = {
            'Subject' : subject,
            'TopicArn': self.config['topic_arn'],
            'Message': message,
            'MessageStructure': 'json',
            'Timestamp' : datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            'AWSAccessKeyId' : self.config['access_key_id'],
            'Action' : 'Publish','SignatureVersion' : '2',
            'SignatureMethod' : 'HmacSHA256',
        }
        query_string = '&'.join(["%s=%s"%(urllib2.quote(key),urllib2.quote(params[key], safe='-_~')) \
                                for key in sorted(params.keys())])
        string_to_sign = '\n'.join(["POST", amazon_host, "/", query_string])
        signature = base64.b64encode(hmac.new(self.config['secret_key'],string_to_sign,digestmod=hashlib.sha256).digest())
        
        url="https://%s/?%s&Signature=%s" % (amazon_host, query_string, urllib2.quote(signature))

        requests.post(url)
