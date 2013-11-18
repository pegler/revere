from revere.sources.base import BaseRevereSource
from sqlalchemy import create_engine


class DatabaseSource(BaseRevereSource):
    name = 'Database'

    def __init__(self, description=None, config={}):
        super(DatabaseSource, self).__init__(description, config)

        required_params = ['connection_string']
        for param in required_params:
            if param not in config or not config[param]:
                raise Exception('Database Source Improperly Configured: missing parameter: %s' % param)
        self.config = config
        self.conn = create_engine(config['connection_string'], pool_recycle=config.get('pool_recycle', 3600))
        self.conn.connect()
        
    def _convert_to_dict(self, row, keys):
        return dict(zip(keys, row))

    def execute(self, sql, as_dict=False):
        result = self.conn.execute(sql)
        if result.rowcount == 0:
            return None

        if as_dict:
            keys = result.keys()
            return [self._convert_to_dict(row, keys) for row in result]

        return result