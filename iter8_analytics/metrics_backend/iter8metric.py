from iter8_analytics.metrics_backend.prometheusquery import PrometheusQuery
import dateutil.parser as parser
from datetime import datetime, timezone, timedelta
from iter8_analytics.metrics_backend.datacapture import DataCapture

class Iter8MetricFactory:
    def __init__(self, metrics_backend_url):
        self.metrics_backend_url = metrics_backend_url

    def get_iter8_metric(self, metric_spec):
        return Iter8Metric(metric_spec, self.metrics_backend_url)

    @staticmethod
    def create_metric_spec(metrics_config, metric_name, entity_tag):
        if metric_name not in metrics_config:
            raise KeyError("Metric name not found in Metrics Configuration")
        metric_spec = {}
        metric_spec["name"] = metric_name
        metric_spec["type"] = metrics_config[metric_name]["type"]
        metric_spec["query_specs"] = []
        for query in metrics_config[metric_name]["query_templates"].keys():
            query_spec = {}
            query_spec["query_name"] = query
            query_spec["query_template"] = metrics_config[metric_name]["query_templates"][query]
            query_spec["zero_value_on_nodata"] = metrics_config[metric_name]["zero_value_on_nodata"]
            query_spec["entity_tags"] = entity_tag
            metric_spec["query_specs"].append(query_spec)
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
        self.type = metric_spec["type"]
        self.query_specs = metric_spec["query_specs"]
        self.metrics_backend_url = metrics_backend_url
        self.prom_queries = [PrometheusQuery(self.metrics_backend_url, query_spec) for query_spec in self.query_specs]

    def get_stats(self, interval_str, offset_str):
        results = {}
        for query in self.prom_queries:
            results[query.query_spec["query_name"]] = query.query_from_template(interval_str, offset_str)
        return results
