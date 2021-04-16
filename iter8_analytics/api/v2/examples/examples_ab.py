"""
Examples used in A/B tests of iter8 analytics v2 APIs.
"""

# iter8 dependencies
from iter8_analytics.api.v2.examples.examples_metrics import \
    request_count, mean_latency, business_revenue

ab_mr_example = [request_count, mean_latency, business_revenue]

ab_er_example = {
    "spec": {
        "strategy": {
            "testingPattern": "A/B"
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
            }],
            "rewards": [{
                "metric": "business-revenue",
                "preferredDirection": "High"
            }]
        }
    },
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "metrics": ab_mr_example
    },
}

ab_am_response = {
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
                    "value": 412.9510489510489
                }
            }
        },
        "business-revenue": {
            "data": {
                "default": {
                    "value": 323.32
                },
                "canary": {
                    "value": 2343.2343
                }
            }
        }
    },
    "message": "All ok"
}

ab_va_response = {
    "data": {
        "default": [
            True
        ],
        "canary": [
            True
        ]
    },
    "message": "All ok"
}

ab_wa_response = {
  "data": {
    "winnerFound": True,
    "winner": "canary",
    "bestVersions": ["canary"]
  },
  "message": "candidate satisfies all objectives"
}

ab_w_response = {
    "data": [{
        "name": "default",
        "value":95

    },{
        "name": "canary",
        "value": 5

    }],
    "message": "All ok"
}

ab_er_example_step1 = {
    "spec": ab_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": ab_am_response
        }
    }
}

ab_er_example_step2 = {
    "spec": ab_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": ab_am_response,
            "versionAssessments": ab_va_response
        }
    }
}

ab_er_example_step3 = {
    "spec": ab_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": ab_am_response,
            "versionAssessments": ab_va_response,
            "winnerAssessment": ab_wa_response
        }
    }
}
