from revere.sources.base import BaseRevereSource
import requests


class GraphiteSource(BaseRevereSource):
    name = 'Graphite'

    def __init__(self, description=None, config={}):
        super(GraphiteSource, self).__init__(description, config)

        required_params = ['url']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('Graphite Source Improperly Configured: missing parameter: %s' % param)
        self.config = config

    def get_datapoints(self, path, from_date=None, to_date=None):

        base_url = self.config['url']

        auth = None

        if self.config.get('auth_username') and self.config.get('auth_password'):
            auth = (self.config.get('auth_username'), self.config.get('auth_password'))

        verify_ssl = self.config.get('verify_ssl', True)

        url = '%s?format=json&target=%s' % (base_url, path)
        if from_date:
            url += '&from=%s' % from_date
        if to_date:
            url += '&to=%s' % to_date

        response = requests.get(url, auth=auth, verify=verify_ssl)
        return response.json()[0]['datapoints']

    def get_sum(self, path, from_date=None, to_date=None):
        """ sum the datapoints in a given range. summing in python is easier than using graphite's integral() function """
        data = self.get_datapoints('%s' % path, from_date, to_date)
        total = reduce(lambda a, b: a + b, [x[0] for x in data if x[0]], 0)
        return total

    def get_avg(self, path, from_date=None, to_date=None):
        """ get the average value for a given range.  null values are counted as 0 """
        data = self.get_datapoints('%s' % path, from_date, to_date)
        total = reduce(lambda a, b: a + b, [x[0] for x in data if x[0]], 0) / float(len(data))
        return total
