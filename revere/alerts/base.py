
class BaseRevereAlert(object):
    name = ''
    
    def __init__(self, description=None, config={}):
        self.description = description