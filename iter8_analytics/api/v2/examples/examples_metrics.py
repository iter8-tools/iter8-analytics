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

# This yaml body is marshalled into the corresponding JSON body.
# body: |
#   {
#     "last": $elapsedTime,
#     "sampling": 600,
#     "filter": "kubernetes.node.name = 'n1' and service = '$name'",
#      "metrics": [
#       {
#         "id": "cpu.cores.used",
#         "aggregations": { "time": "avg", "group": "sum" }
#       }
#     ],
#     "dataSourceType": "container",
#     "paging": {
#       "from": 0,
#       "to": 99
#     }

cpu_utilization = {
    "name": "cpu-utilization",
    "metricObj": {
        "apiVersion": "core.iter8.tools/v2alpha2",
        "kind": "Metric",
        "metadata": {
            "name": "cpu-utilization"
        },
        "spec": {
            "description": "CPU utilization",
            "body": "{\n  \"last\": $elapsedTime,\n  \"sampling\": 600,\n  \"filter\": \"kubernetes.node.name = 'n1' and service = '$name'\",\n   \"metrics\": [\n    {\n      \"id\": \"cpu.cores.used\",\n      \"aggregations\": { \"time\": \"avg\", \"group\": \"sum\" }\n    }\n  ],\n  \"dataSourceType\": \"container\",\n  \"paging\": {\n    \"from\": 0,\n    \"to\": 99\n  }\n}\n",
            "params": [{
                "name": "query",
                "value": "(sum(increase(revision_app_request_latencies_sum{service_name=~'.*$name'}[${elapsedTime}s]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{service_name=~'.*$name'}[${elapsedTime}s])) or on() vector(0))"
            }],
            "type": "gauge",
            "provider": "Sysdig",
            "jqExpression": ".data.result[0].value[1] | tonumber",
            "urlTemplate": "http://metrics-mock:8080/sysdig"
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
