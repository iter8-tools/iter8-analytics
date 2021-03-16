abn_mr_example = [{
    "name": "request-count",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v1alpha3",
        "kind": "Metric",
        "metadata": {
            "name": "request-count"
        },
        "spec": {
            "params": [{
                "name": "query",
                "value": "sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[$interval])) or on() vector(0)"
            }],
            "description": "Number of requests",
            "type": "counter",
            "provider": "prometheus",
            "urlTemplate": "http://prometheus-operated.iter8-monitoring:9090/api/v1/query"
        }
    }},
    {
    "name":"mean-latency",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v1alpha3",
        "kind": "Metric",
        "metadata": {
            "name": "mean-latency"
        },
        "spec": {
            "description": "Mean latency",
            "units": "milliseconds",
            "params": [{
                "name": "query",
                "value": "(sum(increase(revision_app_request_latencies_sum{service_name=~'.*$name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[$interval])) or on() vector(0))"
            }],
            "type": "gauge",
            "sampleSize": {
                "name": "request-count"
            },
            "provider": "prometheus",
            "urlTemplate": "http://prometheus-operated.iter8-monitoring:9090/api/v1/query"
        }
    }},
    {
    "name":"business-revenue",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v1alpha3",
        "kind": "Metric",
        "metadata": {
            "name": "business-revenue"
        },
        "spec": {
            "description": "Business Revenue Metric",
            "units": "dollars",
            "params": [{
                "name": "query",
                "value": "(sum(increase(business_revenue{service_name=~'.*$name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[$interval])) or on() vector(0))"
            }],
            "type": "gauge",
            "sampleSize": {
                "name": "request-count"
            },
            "provider": "prometheus",
            "urlTemplate": "http://prometheus-operated.iter8-monitoring:9090/api/v1/query"
        }
    }}
]
    
abn_er_example = {
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
                    "name": "canary1",
                    "variables": [{
                        "name": "container",
                        "value": "sklearn-iris-22"
                }]
                },
                {
                    "name": "canary2",
                    "variables": [{
                        "name": "container",
                        "value": "sklearn-iris-24"
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
        },
        "metrics": abn_mr_example
    },
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z"
    },
    
}

abn_am_response = {
    "data": {
        "request-count": {
            "data": {
                "default": {
                    "value": 148.0405378277749
                },
                "canary1": {
                    "value": 143.03538837774244
                },
                "canary2": {
                    "value": 145.03478732974244
                }
            }
        },
        "mean-latency": {
            "data": {
                "default": {
                    "value": 419.2027282381035
                },
                "canary1": {
                    "value": 412.9510489510489
                },
                "canary2": {
                    "value": 415.9573489510489
                }
            }
        },
        "business-revenue": {
            "data": {
                "default": {
                    "value": 323.32
                },
                "canary1": {
                    "value": 3343.2343
                },
                "canary2": {
                    "value": 2326.2343
                }
            }
        }
    },
    "message": "All ok"
}

abn_va_response = {
    "data": {
        "default": [
            True
        ],
        "canary1": [
            True
        ],
        "canary2": [
            True
        ]
    },
    "message": "All ok"
}

abn_wa_response = {
  "data": {
    "winnerFound": True,
    "winner": "canary2",
    "bestVersions": ["canary2"]
  },
  "message": "candidate satisfies all objectives"
}

abn_w_response = {
    "data": [{
        "name": "default",
        "value":93

    },{
        "name": "canary1",
        "value": 3

    },{
        "name": "canary2",
        "value": 4

    }],
    "message": "All ok"
}

abn_er_example_step1 = {
    "spec": abn_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": abn_am_response
        }
    }
}

abn_er_example_step2 = {
    "spec": abn_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": abn_am_response,
            "versionAssessments": abn_va_response
        }
    }
}

abn_er_example_step3 = {
    "spec": abn_er_example["spec"],
    "status": {
        "startTime": "2020-04-03T12:55:50.568Z",
        "analysis": {
            "aggregatedMetrics": abn_am_response,
            "versionAssessments": abn_va_response,
            "winnerAssessment": abn_wa_response
        }
    }
}
