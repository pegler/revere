REVERE_SOURCES = {
    'test': {
        'description': 'Test Source',
        'type': 'revere.sources.graphite.GraphiteSource',
        'config': {
        }
    }
}

REVERE_ALERTS = {
    'campfire-eng': {
        'description': 'Post a message to Campfire - Engineering',
        'type': 'revere.alerts.campfire.CampfireAlert',
        'config': {
            'api_token': '',
        }
    }
}