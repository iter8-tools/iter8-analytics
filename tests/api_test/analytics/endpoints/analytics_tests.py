"""Tests for the analytics REST API."""

import unittest
from unittest.mock import Mock
from unittest.mock import patch
from requests.models import Response

import json
from iter8_analytics import app as flask_app
from iter8_analytics.api.analytics import responses as responses
from iter8_analytics.api.analytics import request_parameters as request_parameters
import iter8_analytics.constants as constants
from iter8_analytics.metrics_backend.successcriteria import StatisticalTests, SuccessCriterion
import dateutil.parser as parser

import logging
import os
import requests_mock
import requests
log = logging.getLogger(__name__)

import re

from urllib.parse import urlencode

class TestAnalyticsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup common to all tests."""

        # Initialize the Flask app for testing
        flask_app.app.testing = True
        flask_app.config_logger()
        flask_app.initialize(flask_app.app)

        # Get an internal Flask test client
        cls.flask_test = flask_app.app.test_client()

        cls.backend_url = os.getenv(constants.ITER8_ANALYTICS_METRICS_BACKEND_URL_ENV)
        cls.metrics_endpoint = f'{cls.backend_url}/api/v1/query'
        cls.endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'
        log.info('Completed initialization for all analytics REST API tests.')


    def test_payload_check_and_increment(self):
        """Tests the REST endpoint /analytics/canary/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data_test/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)

            ##################
            # Test request with start_time missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with start_time missing in payload")

            parameters = {
                "baseline": {
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'Missing start_time parameter')
            assert b'\'start_time\' is a required property' in resp.data

            ##################
            # Test request with success_criteria missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with success_criteria missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {

                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'Missing success_criteria missing in payload')

            assert b'\'success_criteria\' is a required property' in resp.data


            ###################
            # Test request with baseline missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with baseline missing in payload")

            parameters = {
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'Baseline missing in payload')

            assert b'\'baseline\' is a required property' in resp.data
            ###################
            # Test request with missing value in success_criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with missing value in success_criteria")


            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 400, 'Missing value in success_criteria')

            assert b'\'value\' is a required property' in resp.data

            ###################
            # Test request with unknown type in success_criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with unknown type in success_criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "normal",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "normal",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 400, 'Unknown type in success_criteria')
            assert b'\'normal\' is not one of [\'delta\', \'threshold\']' in resp.data

            ##################
            # Test request with metric type missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with metric_type missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'success_criteria missing in payload')

            assert b'\'metric_type\' is a required property' in resp.data

            ##################
            # Test request with new metric type in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with new metric_type in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "random",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'new metric_type in payload')

            assert b'\'random\' is not one of [\'Performance\', \'Correctness\']' in resp.data

            ##################
            # Test request with metric_query_template missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with metric_query_template missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'metric_query_template missing in payload')

            assert b'\'metric_query_template\' is a required property' in resp.data


            ##################
            # Test request with metric_sample_size_query_template missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with metric_sample_size_query_template missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'metric_query_template missing in payload')

            assert b'\'metric_sample_size_query_template\' is a required property' in resp.data



    def test_no_data_from_prometheus(self):
        """Tests the REST endpoint /analytics/canary/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data_test/prometheus_no_data_response.json")))

            ###################
            # Test request with no data from prometheus
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data from prometheus")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v1"
                    }
                },
                "canary": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "metric_type": "Correctness",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False,
                            "enable_traffic_control": True,
                            "confidence": 0
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)
