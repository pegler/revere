
class BaseRevereAlert(object):
    name = ''

    def __init__(self, description=None, config={}):
        self.description = description

    def trigger(self, monitor, old_state, new_state, message, return_value):
        pass
