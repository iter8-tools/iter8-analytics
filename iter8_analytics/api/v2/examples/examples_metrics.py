"""
Metric examples used in other examples.
"""
request_count = {
    "name": "request-count",
    "metricObj": {
        "apiVersion": "iter8.tools/v2alpha2",
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
        "apiVersion": "iter8.tools/v2alpha2",
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
        "apiVersion": "iter8.tools/v2alpha2",
        "kind": "Metric",
        "metadata": {
            "name": "cpu-utilization"
        },
        "spec": {
            "description": "CPU utilization",
            "body": "{\n  \"last\": $elapsedTime,\n  \"sampling\": 600,\n  \"filter\": \"kubernetes.node.name = 'n1' and service = '$name'\",\n   \"metrics\": [\n    {\n      \"id\": \"cpu.cores.used\",\n      \"aggregations\": { \"time\": \"avg\", \"group\": \"sum\" }\n    }\n  ],\n  \"dataSourceType\": \"container\",\n  \"paging\": {\n    \"from\": 0,\n    \"to\": 99\n  }\n}\n",
            "method": "POST",
            "type": "gauge",
            "provider": "Sysdig",
            "jqExpression": ".data[0].d[0] | tonumber",
            "urlTemplate": "http://metrics-mock:8080/sysdig"
        }
    }
}

business_revenue = {
    "name": "business-revenue",
    "metricObj": {
        "apiVersion": "iter8.tools/v2alpha2",
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

new_relic_embedded = {
    "apiVersion": "iter8.tools/v2alpha2",
    "kind": "Metric",
    "metadata": {
        "name": "name-count"
    },
    "spec": {
        "params": [
            {
                "name": "nrql",
                "value": "SELECT count(appName) FROM PageView WHERE revisionName='${revision}' SINCE ${elapsedTime} seconds ago"
            }
        ],
        "description": "A New Relic example",
        "type": "Counter",
        "headerTemplates": [
            {
                "name": "X-Query-Key",
                "value": "t0p-secret-api-key"
            }
        ],
        "provider": "newrelic",
                    "jqExpression": ".results[0].count | tonumber",
                    "urlTemplate": "https://insights-api.newrelic.com/v1/accounts/my_account_id"
    }
}

new_relic_secret = {
  "apiVersion": "iter8.tools/v2alpha2",
  "kind": "Metric",
  "metadata": {
    "name": "name-count"
  },
  "spec": {
    "params": [
      {
        "name": "nrql",
        "value": "SELECT count(appName) FROM PageView WHERE revisionName='${revision}' SINCE ${elapsedTime} seconds ago"
      }
    ],
    "description": "A New Relic example",
    "type": "Counter",
    "authType": "APIKey",
    "secret": "myns/nrcredentials",
    "headerTemplates": [
      {
        "name": "X-Query-Key",
        "value": "${mykey}"
      }
    ],
    "provider": "newrelic",
    "jqExpression": ".results[0].count | tonumber",
    "urlTemplate": "https://insights-api.newrelic.com/v1/accounts/my_account_id"
  }
}

sysdig_embedded = {
  "apiVersion": "iter8.tools/v2alpha2",
  "kind": "Metric",
  "metadata": {
    "name": "cpu-utilization"
  },
  "spec": {
    "description": "A Sysdig example",
    "provider": "sysdig",
    "body": "{\n  \"last\": ${elapsedTime},\n  \"sampling\": 600,\n  \"filter\": \"kubernetes.app.revision.name = '${revision}'\",\n  \"metrics\": [\n    {\n      \"id\": \"cpu.cores.used\",\n      \"aggregations\": { \"time\": \"avg\", \"group\": \"sum\" }\n    }\n  ],\n  \"dataSourceType\": \"container\",\n  \"paging\": {\n    \"from\": 0,\n    \"to\": 99\n  }\n}",
    "method": "POST",
    "type": "Gauge",
    "headerTemplates": [
      {
        "name": "Accept",
        "value": "application/json"
      },
      {
        "name": "Authorization",
        "value": "Bearer 87654321-1234-1234-1234-123456789012"
      }
    ],
    "jqExpression": ".data[0].d[0] | tonumber",
    "urlTemplate": "https://secure.sysdig.com/api/data"
  }
}

sysdig_secret = {
  "apiVersion": "iter8.tools/v2alpha2",
  "kind": "Metric",
  "metadata": {
    "name": "cpu-utilization"
  },
  "spec": {
    "description": "A Sysdig example",
    "provider": "sysdig",
    "body": "{\n  \"last\": ${elapsedTime},\n  \"sampling\": 600,\n  \"filter\": \"kubernetes.app.revision.name = '${revision}'\",\n  \"metrics\": [\n    {\n      \"id\": \"cpu.cores.used\",\n      \"aggregations\": { \"time\": \"avg\", \"group\": \"sum\" }\n    }\n  ],\n  \"dataSourceType\": \"container\",\n  \"paging\": {\n    \"from\": 0,\n    \"to\": 99\n  }\n}",
    "method": "POST",
    "authType": "Bearer",
    "secret": "myns/sdcredentials",
    "type": "Gauge",
    "headerTemplates": [
      {
        "name": "Accept",
        "value": "application/json"
      },
      {
        "name": "Authorization",
        "value": "Bearer ${token}"
      }
    ],
    "jqExpression": ".data[0].d[0] | tonumber",
    "urlTemplate": "https://secure.sysdig.com/api/data"
  }
}
