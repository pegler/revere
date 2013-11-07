
class BaseRevereAlert(object):
    name = ''

    def __init__(self, description=None, config={}, enabled_in_config=True):
        self.description = description
        self.enabled_in_config = enabled_in_config

    def trigger(self, monitor, old_state, new_state, message, return_value):
        pass
