"""
Examples used in FastAPI/Swagger documentation of iter8 analytics v2 APIs.
Examples used in tests of iter8 analytics v2 APIs.
"""

er_example = {
    "spec": {
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
    "data": [
        {
            "name": "request-count",
            "versions": [
              {
                  "name": "default",
                  "value": 27.022790513225264
              },
                {
                  "name": "canary",
                  "value": 21.010280639806354
              }
            ]
        },
        {
            "name": "mean-latency",
            "versions": [
                {
                    "name": "default",
                    "value": 347.93841371662717
                },
                {
                    "name": "canary",
                    "value": 526.3333333333333
                }
            ]
        }
    ]
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
