from string import Template
import requests
from requests.auth import HTTPBasicAuth
import logging
import math
from iter8_analytics.metrics_backend.datacapture import DataCapture
import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.constants as constants
from flask import current_app

log = logging.getLogger(__name__)

class PrometheusQuery():
    def __init__(self, prometheus_url, query_spec, authentication=None):
        # TODO ability to set explicit query_spec and authentication is only to 
        # appease prometheusquery_tests.py. This has made the method a bit unweildly
        if prometheus_url:
            self.prometheus_url = prometheus_url + "/api/v1/query"
        else: 
            self.prometheus_url = current_app.config[constants.METRICS_BACKEND_CONFIG_URL] + "/api/v1/query"
        self.query_spec = query_spec
        self.authentication = {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}
        if authentication:
            self.authentication = authentication   
        elif constants.METRICS_BACKEND_CONFIG_AUTH in current_app.config:
            self.authentication = current_app.config[constants.METRICS_BACKEND_CONFIG_AUTH]
        else:
            self.authentication = {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}
        self.auth_type = self.authentication[constants.METRICS_BACKEND_CONFIG_AUTH_TYPE]

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
        log.info(f"backend url is: {self.prometheus_url}")
        # log.info(f"backend url is: {current_app.config['url']}")
        params = {'query': query}
        log.info(params)
        DataCapture.append_value("prometheus_requests", query)

        query_result = None
        log.debug(f"authentication type is: {self.auth_type}")
        if self.auth_type == constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE:
            query_result = requests.get(self.prometheus_url, params=params).json()
        elif self.auth_type == constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC:
            log.debug(f"username is: {self.authentication.get('username')}")
            auth=HTTPBasicAuth(self.authentication.get('username'), self.authentication.get('password'))
            verify = (not self.authentication.get('insecure_skip_verify'))
            log.debug(f"verify is: {verify}")
            query_result = requests.get(self.prometheus_url, params=params, auth=auth, verify=verify).json()
        else:
            # should not happen, validated in app.py, fastapi_app.py
            log.warning(f"Unsupported authentication type: {self.auth_type}; trying {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}")
            query_result = requests.get(self.prometheus_url, params=params).json()

        DataCapture.append_value("prometheus_responses", query_result)
        return self.post_process(query_result)

    def post_process(self, query_result):
        prom_result = {"value": None, "message": ""}
        metric_type_flag = False
        if query_result["status"] != "success":
            prom_result["message"] = "Query did not succeed. Check your query template."
            raise ValueError("Query did not succeed. Check your query template.")
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
                            prom_result["value"] = float("%.3f" % float(each_result["value"][1]))
                            prom_result["message"] = "Query success, result found"
                            return prom_result
                prom_result["message"] = "No matching entity found in Prometheus or result was NaN. Return value based on metric type"
                metric_type_flag = True
        if metric_type_flag == True:
            try:
                return_value = float(self.query_spec[request_parameters.ABSENT_VALUE_STR])
                prom_result["value"] = return_value
            except:
                prom_result["value"] = None
        return prom_result
