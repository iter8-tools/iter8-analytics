ab_mr_example = [{
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
                "value": "sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[${elapsedTime}s])) or on() vector(0)"
            }],
            "description": "Number of requests",
            "type": "counter",
            "provider": "prometheus",
            "jqExpression": ".data.result[0].value[1] | tonumber",
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
                "value": "(sum(increase(revision_app_request_latencies_sum{service_name=~'.*$name'}[${elapsedTime}s]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[${elapsedTime}s])) or on() vector(0))"
            }],
            "type": "gauge",
            "sampleSize": {
                "name": "request-count"
            },
            "provider": "prometheus",
            "jqExpression": ".data.result[0].value[1] | tonumber",
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
                "value": "(sum(increase(business_revenue{service_name=~'.*$name'}[${elapsedTime}s]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[${elapsedTime}s])) or on() vector(0))"
            }],
            "type": "gauge",
            "sampleSize": {
                "name": "request-count"
            },
            "provider": "prometheus",
            "jqExpression": ".data.result[0].value[1] | tonumber",
            "urlTemplate": "http://prometheus-operated.iter8-monitoring:9090/api/v1/query"
        }
    }}
]
    
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