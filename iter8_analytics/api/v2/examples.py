"""
Examples used in FastAPI/Swagger documentation of iter8 analytics v2 APIs.
Examples used in tests of iter8 analytics v2 APIs.
"""

er_example = {
    'spec': {
        'versionInfo': {
            'baseline': {
                'name': 'baseline',
                'tags': {
                    'container': 'sklearn-iris-20'
                }
            },
            'candidates': [
                {
                    'name': 'canary',
                    'tags': {
                        'container': 'sklearn-iris-22'
                    }
                }
            ]
        }
    },
    'status': {
        'startTime': "2020-04-03T12:55:50.568Z"
    }
}

ermr_example = {
    'experimentResource': er_example,
    'metricResources': []
}
