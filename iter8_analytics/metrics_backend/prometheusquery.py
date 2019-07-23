from string import Template
import requests
import logging
import math
from iter8_analytics.metrics_backend.datacapture import DataCapture

log = logging.getLogger(__name__)

class PrometheusQuery():
    def __init__(self, prometheus_url, query_spec):
        self.prometheus_url = prometheus_url + "/api/v1/query"
        self.query_spec = query_spec

    def query_from_template(self, interval_str, offset_str):
        kwargs = {
            "interval": interval_str,  # interval must be interval string
            # offset must be offset string
            "offset_str": f" offset {offset_str}" if offset_str else "",
            "entity_labels": ",".join(self.query_spec["entity_tags"].keys())
        }
        query_template = Template(self.query_spec["query_template"])
        query = query_template.substitute(**kwargs)
        return self.query(query)

    def query(self, query):
        params = {'query': query}
        log.info(query)
        DataCapture.append_value("prometheus_requests", query)
        query_result = requests.get(self.prometheus_url, params=params).json()
        DataCapture.append_value("prometheus_responses", prom_result)
        return self.post_process(query_result)

    def post_process(self, query_result):
        prom_result = {"value": None, "message": ""}
        metric_type_flag = False
        if query_result["status"] != "success":
            prom_result["message"] = "Query did not succeed. Check your query template."
        elif "data" not in query_result:
            prom_result["message"] = "No data found in Prometheus but query succeeded. Check load generator. Returning None"
        else:
            results = query_result["data"]["result"]
            if results == []:
                prom_result["message"] = "No data found in Prometheus but query succeeded. Return value based on metric type"
                metric_type_flag = True
            else:
                match_key = self.query_spec["entity_tags"]
                for each_result in results:
                    if each_result["metric"] == match_key:
                        result_float = float(each_result["value"][1])
                        if not math.isnan(result_float):
                            prom_result["value"] = float(each_result["value"][1])
                            prom_result["message"] = "Query success, result found"
                            return prom_result
                prom_result["message"] = "No matching entity found in Prometheus or result was NaN. Return value based on metric type"
                metric_type_flag = True
        if metric_type_flag == True:
            if self.query_spec["metric_type"] == "Correctness":
                prom_result["value"] = 0
            elif self.query_spec["metric_type"] == "Performance":
                prom_result["value"]= None
        return prom_result
