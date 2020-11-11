"""
Examples used in FastAPI/Swagger documentation of iter8 analytics v2 APIs.
Examples used in tests of iter8 analytics v2 APIs.
"""

er_example = {
    "spec": {
        "strategy": {
            "type": "canary"
        },
        "versionInfo": {
            "baseline": {
                "name": "default",
                "tags": {
                    "container": "sklearn-iris-20"
                }
            },
            "candidates": [
                {
                    "name": "canary",
                    "tags": {
                        "container": "sklearn-iris-22"
                    }
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
        "startTime": "2020-04-03T12:55:50.568Z"
    }
}

mr_example = [{
    "apiVersion": "core.iter8.tools/v1alpha3",
    "kind": "Metric",
    "metadata": {
        "name": "request-count"
    },
    "spec": {
        "params": {
            "query": "sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[$interval])) or on() vector(0)"
        },
        "description": "Number of requests",
        "type": "counter",
        "provider": "prometheus"
    }
}, {
    "apiVersion": "core.iter8.tools/v1alpha3",
    "kind": "Metric",
    "metadata": {
        "name": "mean-latency"
    },
    "spec": {
        "description": "Mean latency",
        "units": "milliseconds",
        "params": {
            "query": "(sum(increase(revision_app_request_latencies_sum{service_name=~'.*$name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[$interval])) or on() vector(0))"
        },
        "type": "gauge",
        "sample_size": {
            "name": "request-count"
        },
        "provider": "prometheus"
    }
}]

ermr_example = {
    'experimentResource': er_example,
    'metricResources': mr_example
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
    "winner": "canary"
  },
  "message": "candidate satisfies all objectives"
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

ermr_example_step1 = {
    'experimentResource': er_example_step1,
    'metricResources': mr_example
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
