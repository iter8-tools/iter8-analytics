"""
Metric examples used in other examples.
"""
request_count = {
    "name": "request-count",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v2alpha2",
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
            "urlTemplate": "http://metrics-mock:8080/promcounter"
        }
    }
}

mean_latency = {
    "name": "mean-latency",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v2alpha2",
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
            "urlTemplate": "http://metrics-mock:8080/promcounter"
        }
    }
}

business_revenue = {
    "name": "business-revenue",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v2alpha2",
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
    }
}
