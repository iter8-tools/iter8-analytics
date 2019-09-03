import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.metrics_backend.prometheusquery import PrometheusQuery
import dateutil.parser as parser
from datetime import datetime, timezone, timedelta
from iter8_analytics.metrics_backend.datacapture import DataCapture

import logging
log = logging.getLogger(__name__)

class Iter8MetricFactory:
    def __init__(self, metrics_backend_url):
        self.metrics_backend_url = metrics_backend_url

    def get_iter8_metric(self, metric_spec):
        return Iter8Metric(metric_spec, self.metrics_backend_url)

    @staticmethod
    def create_metric_spec(criterion, entity_tag):
        metric_spec = {}
        metric_spec["name"] = criterion.metric_name
        metric_spec[request_parameters.METRIC_TYPE_STR] = criterion.metric_type
        metric_spec["query_specs"] = [{"query_name": "value", "query_template": criterion.metric_query_template, request_parameters.METRIC_TYPE_STR: criterion.metric_type, "entity_tags": entity_tag},
        {"query_name": "sample_size", "query_template": criterion.metric_sample_size_query_template, request_parameters.METRIC_TYPE_STR: request_parameters.CORRECTNESS_METRIC_TYPE_STR, "entity_tags": entity_tag}]
        return metric_spec

    @staticmethod
    def get_interval_and_offset_str(start_time, end_time):
        start = parser.parse(start_time)
        end = parser.parse(end_time)
        now = datetime.now(timezone.utc)
        offset_str = ""
        if start <= end:
            interval = max(end - start, timedelta(seconds = 1))
            interval_str = str(int(interval.total_seconds())) + "s"
            if end < now:
                offset = now-end
                if offset.total_seconds() >= 1.0:
                    offset_str = str(int(offset.total_seconds())) + "s"
        else:
            raise ValueError("Start time cannot exceed end time")
        return interval_str,offset_str

class Iter8Metric:
    def __init__(self, metric_spec, metrics_backend_url):
        self.name = metric_spec["name"]
        self.metric_type = metric_spec[request_parameters.METRIC_TYPE_STR]
        self.query_specs = metric_spec["query_specs"]
        self.metrics_backend_url = metrics_backend_url
        self.prom_queries = [PrometheusQuery(self.metrics_backend_url, query_spec) for query_spec in self.query_specs]

    def get_stats(self, interval_str, offset_str):
        results = {responses.STATISTICS_STR: {}, "messages": []}
        for query in self.prom_queries:
            prom_result = query.query_from_template(interval_str, offset_str)
            results[responses.STATISTICS_STR][query.query_spec["query_name"]] = prom_result["value"]
            results["messages"].append(str(query.query_spec["query_name"]+": "+ prom_result["message"]))

        log.debug(results)
        """
        Format of results:
        results = {'statistics': {'sample_size': '12', 'value': 13}, 'messages': ["sample_size: Query success, result found", "value: Query success, result found"]}
        """
        return results
