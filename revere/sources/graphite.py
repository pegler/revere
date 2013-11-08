from revere.sources.base import BaseRevereSource
import requests


class GraphiteSource(BaseRevereSource):
    name = 'Graphite'

    def __init__(self, description=None, config={}):
        super(GraphiteSource, self).__init__(description, config)

        required_params = ['url']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('Graphite Alert Improperly Configured: missing parameter: %s' % param)
        self.config = config

    def get_datapoints(self, path, from_date=None, to_date=None):

        base_url = self.config['url']

        auth = None

        if self.config.get('auth_username') and self.config.get('auth_password'):
            auth = (self.config.get('auth_username'), self.config.get('auth_password'))

        url = '%s?format=json&target=%s' % (base_url, path)
        if from_date:
            url += '&from=%s' % from_date
        if to_date:
            url += '&to=%s' % to_date

        response = requests.get(url, auth=auth)
        return response.json()[0]['datapoints']

    def get_sum(self, path, from_date=None, to_date=None):
        """ apply the integral() graphite function to the path and return the value of the last datapoint """
        data = self.get_datapoints('integral(%s)' % path, from_date, to_date)[-1]
        return data[0]
