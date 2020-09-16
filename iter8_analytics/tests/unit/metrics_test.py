"""Tests for module iter8_analytics.api.analytics.endpoints.metrics"""
# standard python stuff
import logging
import requests_mock
import json
import os
from datetime import timedelta

# iter8 stuff
from iter8_analytics import fastapi_app
from iter8_analytics.api.types import *
import iter8_analytics.constants as constants
import iter8_analytics.config as config
from iter8_analytics.api.metrics import *

env_config = config.get_env_config()
logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'


class TestMetrics:
    def test_prometheus_counter_metric_query(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            versions = [Version(
                id="reviews-v1",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                }), Version(
                id="reviews-v2",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                })
            ]

            query_spec = CounterQuerySpec(
                version_label_keys=versions[0].version_labels.keys(),
                query_template="sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            pcmq = PrometheusCounterMetricQuery(query_spec, versions)
            res = pcmq.query_from_spec(datetime.now(timezone.utc))
            assert 'reviews-v1' in res and 'reviews-v2' in res
            assert len(res) == 2
            assert res['reviews-v1'].value is not None
            assert res['reviews-v2'].value is not None

    def test_prometheus_ratio_metric_query(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            versions = [Version(
                id="reviews-v1",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                }), Version(
                id="reviews-v2",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                }), Version(
                id="reviews-v3",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v3"
                })
            ]

            query_spec = RatioQuerySpec(
                version_label_keys=versions[0].version_labels.keys(),
                numerator_template="sum(increase(istio_requests_total_duration_sec{reporter='source'}[$interval])) by ($version_labels)",
                denominator_template="sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            pcmq = PrometheusRatioMetricQuery(query_spec, versions)
            res = pcmq.query_from_spec(datetime.now(timezone.utc))
            assert len(res) == 3
            assert res['reviews-v1'].value is not None
            assert res['reviews-v2'].value is not None
            assert res['reviews-v3'].value is not None

    def test_get_counter_metrics(self):
        counter_metric_specs = {
            "iter8_request_count":  CounterMetricSpec(** {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            }),
            "iter8_total_latency": CounterMetricSpec(** {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            }),
            "iter8_error_count": CounterMetricSpec(** {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            }),
            "conversion_count": CounterMetricSpec(** {
                "id": "conversion_count",
                "query_template": "sum(increase(newsletter_signups[$interval])) by ($version_labels)"
            })
        }

        versions = [Version(
            id="reviews-v1",
            version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }), Version(
            id="reviews-v2",
            version_labels={
                "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                    }), Version(
            id="reviews-v3",
            version_labels={
                "destination_service_namespace": "default",
                "destination_workload": "reviews-v3"
            })
        ]

        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            cm = get_counter_metrics(
                counter_metric_specs,
                versions,
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

            assert len(cm) == 3
            for version in cm:
                for metric in cm[version]:
                    assert cm[version][metric].value is not None

    def test_get_ratio_metrics(self):
        counter_metric_specs = {
            "iter8_request_count":  CounterMetricSpec(** {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            }),
            "iter8_total_latency": CounterMetricSpec(** {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            }),
            "iter8_error_count": CounterMetricSpec(** {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            }),
            "conversion_count": CounterMetricSpec(** {
                "id": "conversion_count",
                "query_template": "sum(increase(newsletter_signups[$interval])) by ($version_labels)"
            })
        }

        ratio_metric_specs = {
            "iter8_mean_latency": RatioMetricSpec(** {
                "id": "iter8_mean_latency",
                "numerator": "iter8_total_latency",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower",
                "zero_to_one": False
            }),
            "iter8_error_rate": RatioMetricSpec(** {
                "id": "iter8_error_rate",
                "numerator": "iter8_error_count",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower",
                "zero_to_one": True
            }),
            "conversion_rate":  RatioMetricSpec(** {
                "id": "conversion_rate",
                "numerator": "conversion_count",
                "denominator": "iter8_request_count",
                "preferred_direction": "higher",
                "zero_to_one": False
            })
        }

        versions = [Version(
            id="reviews-v1",
            version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }), Version(
            id="reviews-v2",
            version_labels={
                "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                    }), Version(
            id="reviews-v3",
            version_labels={
                "destination_service_namespace": "default",
                "destination_workload": "reviews-v3"
            }), Version(
            id="reviews-v4",
            version_labels={
                "destination_service_namespace": "default",
                "destination_workload": "reviews-v4"
            })
        ]

        def match_newsletter_query(req):
            return "newsletter_signups" in req.path_url and "istio_requests_total" in req.path_url

        def match_non_newsletter_query(req):
            return not ("newsletter_signups" in req.path_url and "istio_requests_total" in req.path_url)

        with requests_mock.mock(real_http=True) as m:
            file_path_resp = os.path.join(os.path.dirname(
                __file__), 'data/prom_responses', 'prometheus_sample_response.json')

            file_path_no_resp = os.path.join(os.path.dirname(
                __file__), 'data/prom_responses', 'prometheus_no_data_response.json')

            m.register_uri('GET', metrics_endpoint, json=json.load(
                open(file_path_resp)), additional_matcher=match_non_newsletter_query)

            m.register_uri('GET', metrics_endpoint, json=json.load(
                open(file_path_no_resp)), additional_matcher=match_newsletter_query)

            cm = get_counter_metrics(
                counter_metric_specs,
                versions,
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

            rm = get_ratio_metrics(
                ratio_metric_specs,
                counter_metric_specs,
                cm,
                versions,
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

            assert len(rm) == 4
            for version in rm:
                for metric in rm[version]:
                    if version != "reviews-v4":
                        assert rm[version][metric].value is not None
                        if metric == 'conversion_rate':
                            assert rm[version][metric].value == 0.0
                    else:
                        assert rm[version][metric].value is None

    def test_prom_exception(self):
        def bad_json(request, context):
            raise HTTPException(status_code=422, detail="Bad JSON")

        with requests_mock.mock(real_http=True) as m:
            m.get(metrics_endpoint, json=bad_json)

            versions = [Version(
                id="reviews-v1",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                }), Version(
                id="reviews-v2",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                })
            ]

            query_spec = CounterQuerySpec(
                version_label_keys=versions[0].version_labels.keys(),
                query_template="sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            try:
                pcmq = PrometheusCounterMetricQuery(query_spec, versions)
                res = pcmq.query_from_spec(datetime.now(timezone.utc))
            except HTTPException as he:
                pass

    def test_unsuccessful_prom(self):
        with requests_mock.mock(real_http=True) as m:
            m.get(metrics_endpoint, json={
                "status": "failure"
            })

            versions = [Version(
                id="reviews-v1",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                }), Version(
                id="reviews-v2",
                version_labels={
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v2"
                })
            ]

            query_spec = CounterQuerySpec(
                version_label_keys=versions[0].version_labels.keys(),
                query_template="sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1)
            )

            try:
                pcmq = PrometheusCounterMetricQuery(query_spec, versions)
                res = pcmq.query_from_spec(datetime.now(timezone.utc))
            except HTTPException as he:
                pass

            m.get(metrics_endpoint, json={
                "status": "success"
            })

            try:
                pcmq = PrometheusCounterMetricQuery(query_spec, versions)
                res = pcmq.query_from_spec(datetime.now(timezone.utc))
            except HTTPException as he:
                pass

            m.get(metrics_endpoint, json={
                "status": "success",
                "data": {
                    "resultType": "scalar"
                }
            })

            try:
                pcmq = PrometheusCounterMetricQuery(query_spec, versions)
                res = pcmq.query_from_spec(datetime.now(timezone.utc))
            except HTTPException as he:
                pass

    def test_new_ratio_max_min(self):

        metric_id_to_list_of_values = {
            "metric1": [0.1, 0.2, 0.3],
            "metric2": [0.2],
            "metric3": []
        }

        nrmm = new_ratio_max_min(metric_id_to_list_of_values)
        logger.debug(nrmm)
        assert len(nrmm) == 3
        assert nrmm["metric1"] == RatioMaxMin(minimum=0.1, maximum=0.3)
        assert nrmm["metric2"] == RatioMaxMin(minimum=0.2, maximum=0.2)
        assert nrmm["metric3"] == RatioMaxMin()
