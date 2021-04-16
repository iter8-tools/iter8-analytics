"""
Examples used in FastAPI/Swagger documentation of iter8 analytics v2 APIs.
Examples used in tests of iter8 analytics v2 APIs.
"""
# iter8 dependencies
from iter8_analytics.api.v2.examples.examples_metrics import \
    request_count, mean_latency

mr_example = [request_count, mean_latency]

er_example = {
    "spec": {
        "strategy": {
            "testingPattern": "Canary"
        },
        "versionInfo": {
            "baseline": {
                "name": "default",
                "variables": [{
                    "name": "container",
                    "value": "sklearn-iris-20"
                }]
            },
            "candidates": [
                {
                    "name": "canary",
                    "variables": [{
                        "name": "container",
                        "value": "sklearn-iris-22"
                }]
                }
            ]
        },
        "criteria": {
            "objectives": [{
                "metric": "mean-latency",
                "upperLimit": 420.0
            }]
        }
    },
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "metrics": mr_example
    },
}

am_response = {
    "data": {
        "request-count": {
            "data": {
                "default": {
                    "value": 148.0405378277749
                },
                "canary": {
                    "value": 143.03538837774244
                }
            }
        },
        "mean-latency": {
            "data": {
                "default": {
                    "value": 419.2027282381035
                },
                "canary": {
                    "value": 426.9510489510489
                }
            }
        }
    },
    "message": "All ok"
}

va_response = {
    "data": {
        "default": [
            True
        ],
        "canary": [
            False
        ]
    },
    "message": "All ok"
}

wa_response = {
  "data": {
    "winnerFound": True,
    "winner": "canary",
    "bestVersions": ["canary"]
  },
  "message": "candidate satisfies all objectives"
}

w_response = {
    "data": [{
        "name": "default",
        "value":95

    },{
        "name": "canary",
        "value": 5

    }],
    "message": "All ok"
}

er_example_step1 = {
    "spec": er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": am_response
        }
    }
}

er_example_step2 = {
    "spec": er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": am_response,
            "versionAssessments": va_response
        }
    }
}

er_example_step3 = {
    "spec": er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": am_response,
            "versionAssessments": va_response,
            "winnerAssessment": wa_response
        }
    }
}
