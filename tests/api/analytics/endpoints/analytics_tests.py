"""Tests for the analytics REST API."""

import unittest
from unittest.mock import Mock
from unittest.mock import patch
from requests.models import Response
from fastapi.testclient import TestClient

import json
from iter8_analytics import app as flask_app
from iter8_analytics import fastapi_app

from iter8_analytics.api.analytics.experiment_iteration_request import ExperimentIterationParameters
from iter8_analytics.api.analytics.experiment_iteration_response import Iter8AssessmentAndRecommendation

from iter8_analytics.api.analytics import responses
from iter8_analytics.api.analytics import request_parameters

import iter8_analytics.constants as constants
from iter8_analytics.api.analytics.successcriteria import StatisticalTests, SuccessCriterion
import dateutil.parser as parser
from collections import namedtuple

import logging
import os
import requests_mock
import requests
log = logging.getLogger(__name__)

import re

from urllib.parse import urlencode

class TestAnalyticsNamespaceAPI(unittest.TestCase):
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
        #cls.metrics_endpoint = f'http://localhost:9090/api/v1/query'
        log.info('Completed initialization for all analytics REST API tests.')

    ##All tests after this involve the /analytics/canary/check_and_increment endpoint (until mentioned otherwise)
    def test_payload_canary_check_and_increment(self):
        """Tests the REST endpoint /analytics/canary/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request with no change observed wrt sample size or metric parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 75,
                        "success_criterion_information": [
                            [0,0]]
                        },
                    "candidate": {
                        "traffic_percentage": 25,
                        "success_criterion_information": [
                            [0,0]]
                        }
                    }
                }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            correct_response = {"baseline":{"traffic_percentage":73.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":27,"success_criterion_information":[[19,19.677]]}}
            self.assertEqual(resp.status_code, 200, resp.data)

            self.assertEqual(resp.get_json()["_last_state"], correct_response)


            ##################
            # Test request with start_time missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with start_time missing in payload")

            parameters = {
                "baseline": {
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
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
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "sample_size": 0,
                            "stop_on_failure": False
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
            # Test request with Unknown type in is_counter
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with Unknown type in is_counter")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": "No",
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "normal",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 400, 'Unknown type in is_counter')

            assert b"\'No\' is not of type \'boolean\'" in resp.data
            assert b'\'normal\' is not one of [\'delta\', \'threshold\']' in resp.data

            ##################
            # Test request with metric type missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with is_counter missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
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
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'is_counter missing in payload')

            assert b'\'is_counter\' is a required property' in resp.data
            #assert b'\'absent_value\' is a required property' in resp.data

            ##################
            # Test request with absent value of type float in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with absent value of type float in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": 0,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'new absent_value type in payload')
            assert b'0 is not of type \'string\'' in resp.data

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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

            ##################
            # Test request threshold crossing in a counter metric
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with metric_sample_size_query_template missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 18,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            assert resp.get_json()["assessment"]["summary"]["abort_experiment"]
            assert not resp.get_json()["assessment"]["summary"]["all_success_criteria_met"]


            ##################
            # Test request delta criterion with counter metric
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with metric_sample_size_query_template missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.5,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            assert b'Delta criterion cannot be used with counter metric.' in resp.data


    def test_baseline_failing_success_criteria(self):
        """Tests the REST endpoint /analytics/canary/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_baseline_failing_response.json")))

            ###################
            # Test request when both candidate and baseline fail success criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when both candidate and baseline fail success criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 2,
                            "stop_on_failure": False
                        },
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.1,
                            "sample_size": 2,
                            "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage":98.0,
                        "success_criterion_information":[[1,0.0]]
                        },
                    "candidate": {
                        "traffic_percentage":2,
                        "success_criterion_information":[[1,0.0]]
                        }
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            assert 'The baseline version did not meet success criteria' in resp.get_json()["assessment"]["summary"]["conclusions"]




    def test_no_data_from_prometheus(self):
        """Tests the REST endpoint /analytics/canary/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_no_data_response.json")))

            ###################
            # Test request with no data from prometheus- iter8_error_count
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data from prometheus")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request with no data from prometheus- iter8_latency
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data from prometheus")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_latency",
                            "is_counter": False,
                            "absent_value": "None",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /analytics/canary/epsilon_t_greedy endpoint
    def test_payload_canary_epsilon_t_greedy(self):
        """Tests the REST endpoint /analytics/canary/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ##################
            # Test request with pre filled last state in payload on iteration 4
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "end_time": "2019-04-24T20:30:02.389Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "end_time": "2019-04-24T20:30:02.389Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "max_traffic_percent": 100,
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 13,
                        "success_criterion_information": [
                            [
                            1,
                            2
                            ]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 87,
                        "success_criterion_information": [
                            [
                            2,
                            3
                            ]
                        ]
                        },
                    "effective_iteration_count": 4
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {"baseline":{"traffic_percentage":10.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":90,"success_criterion_information":[[19,19.677]]},"effective_iteration_count":5}
            self.assertEqual(resp.get_json()["_last_state"], correct_response)


            ##################
            # Test request with pre filled last state in payload on iteration 5- when no change is observed
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [21,21.764]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [19,19.677]
                        ]
                        },
                    "effective_iteration_count": 5
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {"baseline":{"traffic_percentage":10.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":90,"success_criterion_information":[[19,19.677]]},"effective_iteration_count":5}
            self.assertEqual(resp.get_json()["_last_state"], correct_response)

    # Test request when candidate fails success criteria
    def test_candidate_failing_success_criteria(self):
        """Tests the REST endpoint /analytics/canary/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_baseline_failing_response.json")))

            ###################
            # Test request when both candidate and baseline fail success criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when both candidate and baseline fail success criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 1,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "effective_iteration_count": 3
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            assert 'The baseline version did not meet success criteria' in resp.get_json()["assessment"]["summary"]["conclusions"]



            ###################
            # Test request when candidate fails success criteria because sample size requirements are not met
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when both candidate and baseline fail success criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 10,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "effective_iteration_count": 3
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {'baseline': {'traffic_percentage': 90.0, 'success_criterion_information': [[4, 4.0]]}, 'candidate': {'traffic_percentage': 10, 'success_criterion_information': [[5, 5.0]]}, 'effective_iteration_count': 3}
            self.assertEqual(correct_response, resp.get_json()["_last_state"])

    #All tests after this involve the /analytics/canary/posterior_bayesian_routing endpoint
    def test_payload_canary_posterior_bayesian_routing(self):
        """Tests the REST endpoint /analytics/canary/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request to check for default parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request to with stop on failure=True
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 19,
                        "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            correct_response = ["The experiment needs to be aborted", "All success criteria were not met", "Required confidence of 0.95 was not reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])
            self.assertEqual(resp.status_code, 200, resp.data)


    def test_payload_canary_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /analytics/canary/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response_br.json")))

            ###################
            # Test request with high sample size for high confidence results
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])


            ###################
            # Test request with high sample size for high confidence results + multiple metrics
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        },
                    {
                        "metric_name": "iter8_error_count",
                        "is_counter": True,
                        "absent_value": "0",
                        "min_max": {
                            "min": 0,
                            "max": 1
                         },
                         "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "type": "threshold",
                         "value": 200000,
                         "stop_on_failure": False
                         }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])



    #All tests after this involve the /analytics/canary/optimistic_bayesian_routing endpoint
    def test_payload_canary_optimistic_bayesian_routing(self):
        """Tests the REST endpoint /analytics/canary/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request to check for default parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request to with stop on failure=True
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 19,
                        "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            correct_response = ["The experiment needs to be aborted", "All success criteria were not met", "Required confidence of 0.95 was not reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])
            self.assertEqual(resp.status_code, 200, resp.data)


    def test_payload_canary_optimistic_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /analytics/canary/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response_br.json")))

            ###################
            # Test request with high sample size for high confidence results
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            log.info(f"{resp.data}")
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])


            ###################
            # Test request with high sample size for high confidence results + multiple metrics
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        },
                    {
                        "metric_name": "iter8_error_count",
                        "is_counter": True,
                        "absent_value": "0",
                        "min_max": {
                            "min": 0,
                            "max": 1
                         },
                         "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "type": "threshold",
                         "value": 200000,
                         "stop_on_failure": False
                         }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])

    def test_no_data_canary_optimistic_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /analytics/canary/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_no_data_response.json")))

            ###################
            # Test request with no data for obr (first iteration)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request with no data for obr (not first iteration + min-max available)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data for obr (not first iteration + min-max available)")

            params = namedtuple('params', 'alpha beta gamma sigma')
            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "None",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "success_criterion_belief": [params(1, 1, None, None)],
                        "reward_belief": params(None, None, None, None)
                    },
                    "candidate": {
                        "success_criterion_belief": [params(1, 1, None, None)],
                        "reward_belief": params(None, None, None, None)
                    }
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request with no data for obr (not first iteration + min-max not available)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data for obr (not first iteration + min-max not available)")

            params = namedtuple('params', 'alpha beta gamma sigma')
            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "None",
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "success_criterion_belief": [params(None, None, 0, 1)],
                        "reward_belief": params(None, None, None, None)
                    },
                    "candidate": {
                        "success_criterion_belief": [params(None, None, 0, 1)],
                        "reward_belief": params(None, None, None, None)
                    }
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


    ##All tests after this involve the /analytics/canary/check_and_increment endpoint for A/B experiments
    def test_payload_ab_check_and_increment(self):
        """Tests the REST endpoint /analytics/ab/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /analytics/canary/epsilon_t_greedy endpoint for A/B experiments
    def test_payload_ab_epsilon_t_greedy(self):
        """Tests the REST endpoint /analytics/ab/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
            }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /analytics/canary/posterior_bayesian_routing endpoint for A/B experiments
    def test_payload_ab_posterior_bayesian_routing(self):
        """Tests the REST endpoint /analytics/ab/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


    #All tests after this involve the /analytics/canary/optimistic_bayesian_routing endpoint for A/B experiments
    def test_payload_ab_optimistic_bayesian_routing(self):
        """Tests the REST endpoint /analytics/ab/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/analytics/canary/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


#############################################################
##The next tests use the Experiment namespace which will be retained after a controller fix
#############################################################

    ##All tests after this involve the /experiment/check_and_increment endpoint (until mentioned otherwise)
    def test_payload_experiment_canary_check_and_increment(self):
        """Tests the REST endpoint /experiment/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/experiment/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request with no change observed wrt sample size or metric parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no change observed wrt sample size or metric parameters")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 75,
                        "success_criterion_information": [
                            [0,0]]
                        },
                    "candidate": {
                        "traffic_percentage": 25,
                        "success_criterion_information": [
                            [0,0]]
                        }
                    }
                }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            correct_response = {"baseline":{"traffic_percentage":73.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":27,"success_criterion_information":[[19,19.677]]}}
            self.assertEqual(resp.status_code, 200, resp.data)

            self.assertEqual(resp.get_json()["_last_state"], correct_response)


            ##################
            # Test request with start_time missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with start_time missing in payload")

            parameters = {
                "baseline": {
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
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
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "sample_size": 0,
                            "stop_on_failure": False
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
            # Test request with Unknown type in is_counter
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with Unknown type in is_counter")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": "No",
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "normal",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 400, 'Unknown type in is_counter')

            assert b"\'No\' is not of type \'boolean\'" in resp.data
            assert b'\'normal\' is not one of [\'delta\', \'threshold\']' in resp.data

            ##################
            # Test request with is_counter missing in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with is_counter missing in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
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
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'is_counter missing in payload')

            assert b'\'is_counter\' is a required property' in resp.data
            #assert b'\'absent_value\' is a required property' in resp.data

            ##################
            # Test request with absent value of type float in payload
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with absent value of type float in payload")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": 0,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            # We should get a BAD REQUEST HTTP error
            self.assertEqual(resp.status_code, 400, 'new absent_value type in payload')
            assert b'0 is not of type \'string\'' in resp.data

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
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

            ##################
            # Test request threshold crossing in a counter metric
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request threshold crossing in a counter metric")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 18,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            assert resp.get_json()["assessment"]["summary"]["abort_experiment"]
            assert not resp.get_json()["assessment"]["summary"]["all_success_criteria_met"]


            ##################
            # Test request delta criterion with counter metric
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request delta criterion with counter metric")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.5,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }
            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            assert b'Delta criterion cannot be used with counter metric.' in resp.data


    def test_experiment_baseline_failing_success_criteria(self):
        """Tests the REST endpoint /experiment/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/experiment/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_baseline_failing_response.json")))

            ###################
            # Test request when both candidate and baseline fail success criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when both candidate and baseline fail success criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 2,
                            "stop_on_failure": False
                        },
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.1,
                            "sample_size": 2,
                            "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage":98.0,
                        "success_criterion_information":[[1,0.0]]
                        },
                    "candidate": {
                        "traffic_percentage":2,
                        "success_criterion_information":[[1,0.0]]
                        }
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            assert 'The baseline version did not meet success criteria' in resp.get_json()["assessment"]["summary"]["conclusions"]




    def test_experiment_no_data_from_prometheus(self):
        """Tests the REST endpoint /experiment/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/experiment/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_no_data_response.json")))

            ###################
            # Test request with no data from prometheus- iter8_error_count
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data from prometheus")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request with no data from prometheus- iter8_latency
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data from prometheus")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_latency",
                            "is_counter": False,
                            "absent_value": "None",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)

            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /experiment/epsilon_t_greedy endpoint
    def test_experiment_payload_canary_epsilon_t_greedy(self):
        """Tests the REST endpoint /experiment/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/experiment/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
            }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ##################
            # Test request with pre filled last state in payload on iteration 4
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with pre filled last state in payload on iteration 4")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "end_time": "2019-04-24T20:30:02.389Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "end_time": "2019-04-24T20:30:02.389Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "max_traffic_percent": 100,
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 13,
                        "success_criterion_information": [
                            [
                            1,
                            2
                            ]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 87,
                        "success_criterion_information": [
                            [
                            2,
                            3
                            ]
                        ]
                        },
                    "effective_iteration_count": 4
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {"baseline":{"traffic_percentage":10.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":90,"success_criterion_information":[[19,19.677]]},"effective_iteration_count":5}
            self.assertEqual(resp.get_json()["_last_state"], correct_response)


            ##################
            # Test request with pre filled last state in payload on iteration 5- when no change is observed
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with pre filled last state in payload on iteration 5- when no change is observed")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [21,21.764]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [19,19.677]
                        ]
                        },
                    "effective_iteration_count": 5
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {"baseline":{"traffic_percentage":10.0,"success_criterion_information":[[21,21.764]]},"candidate":{"traffic_percentage":90,"success_criterion_information":[[19,19.677]]},"effective_iteration_count":5}
            self.assertEqual(resp.get_json()["_last_state"], correct_response)

    # Test request when candidate fails success criteria
    def test_experiment_candidate_failing_success_criteria(self):
        """Tests the REST endpoint /experiment/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/experiment/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_baseline_failing_response.json")))

            ###################
            # Test request when both candidate and baseline fail success criteria
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when both candidate and baseline fail success criteria")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 1,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "effective_iteration_count": 3
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            assert 'The baseline version did not meet success criteria' in resp.get_json()["assessment"]["summary"]["conclusions"]



            ###################
            # Test request when candidate fails success criteria because sample size requirements are not met
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request when candidate fails success criteria because sample size requirements are not met")

            parameters = {
                "baseline": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_count",
                            "is_counter": True,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "threshold",
                            "value": 2,
                            "sample_size": 10,
                            "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "traffic_percentage": 90,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "candidate": {
                        "traffic_percentage": 10,
                        "success_criterion_information": [
                            [1,0.0]
                        ]
                        },
                    "effective_iteration_count": 3
                    }
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = {'baseline': {'traffic_percentage': 90.0, 'success_criterion_information': [[4, 4.0]]}, 'candidate': {'traffic_percentage': 10, 'success_criterion_information': [[5, 5.0]]}, 'effective_iteration_count': 3}
            self.assertEqual(correct_response, resp.get_json()["_last_state"])

    #All tests after this involve the /experiment/posterior_bayesian_routing endpoint
    def test_experiment_payload_canary_posterior_bayesian_routing(self):
        """Tests the REST endpoint /experiment/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request to check for default parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request to check for default parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request to with stop on failure=True
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request to with stop on failure=True")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 19,
                        "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            correct_response = ["The experiment needs to be aborted", "All success criteria were not met", "Required confidence of 0.95 was not reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])
            self.assertEqual(resp.status_code, 200, resp.data)


    def test_experiment_payload_canary_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /experiment/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response_br.json")))

            ###################
            # Test request with high sample size for high confidence results
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with high sample size for high confidence results")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])


            ###################
            # Test request with high sample size for high confidence results + multiple metrics
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with high sample size for high confidence results + multiple metrics")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        },
                    {
                        "metric_name": "iter8_error_count",
                        "is_counter": True,
                        "absent_value": "0",
                        "min_max": {
                            "min": 0,
                            "max": 1
                         },
                         "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "type": "threshold",
                         "value": 200000,
                         "stop_on_failure": False
                         }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])



    #All tests after this involve the /experiment/optimistic_bayesian_routing endpoint
    def test_experiment_payload_canary_optimistic_bayesian_routing(self):
        """Tests the REST endpoint /experiment/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


            ###################
            # Test request to check for default parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request to check for default parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request to with stop on failure=True
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request to with stop on failure=True")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_service_namespace": "default",
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 19,
                        "stop_on_failure": True
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            correct_response = ["The experiment needs to be aborted", "All success criteria were not met", "Required confidence of 0.95 was not reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])
            self.assertEqual(resp.status_code, 200, resp.data)


    def test_experiment_payload_canary_optimistic_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /experiment/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response_br.json")))

            ###################
            # Test request with high sample size for high confidence results
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with high sample size for high confidence results")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])


            ###################
            # Test request with high sample size for high confidence results + multiple metrics
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with high sample size for high confidence results + multiple metrics")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        },
                    {
                        "metric_name": "iter8_error_count",
                        "is_counter": True,
                        "absent_value": "0",
                        "min_max": {
                            "min": 0,
                            "max": 1
                         },
                         "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                         "type": "threshold",
                         "value": 200000,
                         "stop_on_failure": False
                         }
                    ]
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)
            correct_response = ["All success criteria were  met", "Required confidence of 0.5 was reached"]
            self.assertEqual(correct_response, resp.get_json()["assessment"]["summary"]["conclusions"])

    def test_experiment_no_data_canary_optimistic_bayesian_routing_high_sample_size(self):
        """Tests the REST endpoint /experiment/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_no_data_response.json")))

            ###################
            # Test request with no data for obr (first iteration)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data for obr (first iteration)")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {}
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request with no data for obr (not first iteration + min-max available)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data for obr (not first iteration + min-max available)")

            params = namedtuple('params', 'alpha beta gamma sigma')
            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "None",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "success_criterion_belief": [params(1, 1, None, None)],
                        "reward_belief": params(None, None, None, None)
                    },
                    "candidate": {
                        "success_criterion_belief": [params(1, 1, None, None)],
                        "reward_belief": params(None, None, None, None)
                    }
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

            ###################
            # Test request with no data for obr (not first iteration + min-max not available)
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with no data for obr (not first iteration + min-max not available)")

            params = namedtuple('params', 'alpha beta gamma sigma')
            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.5,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "None",
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 200000,
                        "stop_on_failure": False
                        }
                    ]
                },
                "_last_state": {
                    "baseline": {
                        "success_criterion_belief": [params(None, None, 0, 1)],
                        "reward_belief": params(None, None, None, None)
                    },
                    "candidate": {
                        "success_criterion_belief": [params(None, None, 0, 1)],
                        "reward_belief": params(None, None, None, None)
                    }
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

    ##All tests after this involve the /experiment/check_and_increment endpoint for A/B experiments
    def test_experiment_payload_ab_check_and_increment(self):
        """Tests the REST endpoint /experiment/check_and_increment."""

        endpoint = f'http://localhost:5555/api/v1/experiment/check_and_increment'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
            }

            # Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /experiment/epsilon_t_greedy endpoint for A/B experiments
    def test_experiment_payload_ab_epsilon_t_greedy(self):
        """Tests the REST endpoint /experiment/epsilon_t_greedy."""

        endpoint = f'http://localhost:5555/api/v1/experiment/epsilon_t_greedy'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

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
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                    "start_time": "2019-04-24T19:40:32.017Z",
                    "tags": {
                        "destination_service_namespace": "default",
                        "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                    "success_criteria": [
                        {
                            "metric_name": "iter8_error_rate",
                            "is_counter": False,
                            "absent_value": "0.0",
                            "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                            "type": "delta",
                            "value": 0.02,
                            "sample_size": 0,
                            "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {}
            }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)

    #All tests after this involve the /experiment/posterior_bayesian_routing endpoint for A/B experiments
    def test_experiment_payload_ab_posterior_bayesian_routing(self):
        """Tests the REST endpoint /experiment/posterior_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/posterior_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)


    #All tests after this involve the /experiment/optimistic_bayesian_routing endpoint for A/B experiments
    def test_experimentp_ayload_ab_optimistic_bayesian_routing(self):
        """Tests the REST endpoint /experiment/optimistic_bayesian_routing."""

        endpoint = f'http://localhost:5555/api/v1/experiment/optimistic_bayesian_routing'

        with requests_mock.mock() as m:
            m.get(self.metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            ###################
            # Test request with some required parameters
            ###################
            log.info("\n\n\n")
            log.info('===TESTING ENDPOINT {endpoint}'.format(endpoint=endpoint))
            log.info("Test request with some required parameters")

            parameters = {
                "baseline": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v1"
                    }
                },
                "candidate": {
                "start_time": "2019-05-01T19:00:02.389Z",
                "tags": {
                    "destination_workload": "reviews-v3"
                    }
                },
                "traffic_control": {
                   "confidence": 0.9,
                   "success_criteria": [
                   {
                       "metric_name": "iter8_error_rate",
                       "is_counter": False,
                       "absent_value": "0",
                       "min_max": {
                           "min": 0,
                           "max": 1
                        },
                        "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": False
                        }
                    ],
                    "reward": {
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)"
                    }
                },
                "_last_state": {
                }
                }

            #Call the REST API via the test client
            resp = self.flask_test.post(endpoint, json=parameters)
            self.assertEqual(resp.status_code, 200, resp.data)



class TestUnifiedAnalyticsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup common to all tests in this class"""

        cls.client = TestClient(fastapi_app.app)
        log.info('Completed initialization for FastAPI based  REST API tests')

    def test_fastapi(self):
        # fastapi endpoint
        endpoint = "/assessment"

        # fastapi post data
        _experiment_iteration_parameters = {
            'start_time': "2020-04-03T12:55:50.568Z",
            'iteration_number': 1, 
            'service_name': "reviews",
            "metric_specs": {
                "counter_metrics": [
                    {
                        "id": "iter8_request_count",
                        "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($entity_labels)"
                    },
                    {
                        "id": "iter8_total_latency",
                        "query_template": "sum(increase(istio_request_duration_seconds_sum{reporter='source'}[$interval])) by ($entity_labels)"
                    },
                    {
                        "id": "iter8_error_count",
                        "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($entity_labels)",
                        "preferred_direction": "lower"
                    },
                    {
                        "id": "conversion_count",
                        "query_template": "sum(increase(newsletter_signups[$interval])) by ($entity_labels)"
                    },
                ],
                "ratio_metrics": [
                    {
                        "id": "iter8_mean_latency",
                        "numerator": "iter8_total_latency",
                        "denominator": "iter8_request_count",
                        "preferred_direction": "lower",
                        "unit_range": False
                    },
                    {
                        "id": "iter8_error_rate",
                        "numerator": "iter8_error_count",
                        "denominator": "iter8_request_count",
                        "preferred_direction": "lower",
                        "unit_range": True
                    },
                    {
                        "id": "conversion_rate",
                        "numerator": "conversion_count",
                        "denominator": "iter8_request_count",
                        "preferred_direction": "higher",
                        "unit_range": True
                    }
                ]},
            "criteria": [
                {
                    "id": "0",
                    "metric_id": "iter8_mean_latency",
                    "reward": False,
                    "threshold": {
                        "type": "absolute",
                        "value": 25
                    }
                }
            ],
            "baseline": {
                "id": "reviews_base",
                "version_labels": {
                    'destination_service_namespace': "bookinfo_ns",
                    'destination_workload': "reviews-v1"
                }
            },
            "candidates": [
                {
                    "id": "reviews_candidate",
                    "version_labels": {
                        'destination_service_namespace': "bookinfo_ns",
                        'destination_workload': "reviews-v2"
                    }
                }
            ],
            "advanced_traffic_control_parameters": {
                "exploration_traffic_percentage": 5.0,
                "check_and_increment_parameters": {
                    "step_size": 1
                }
            },
            "advanced_assessment_parameters": {
                "posterior_probability_for_credible_intervals": 95.0,
                "min_posterior_probability_for_winner": 99.0
            }
        }

        eip = ExperimentIterationParameters(** _experiment_iteration_parameters)

        log.info("\n\n\n")
        log.info('===TESTING FASTAPI ENDPOINT')
        log.info("Test request with some required parameters")

        # Call the FastAPI endpoint via the test client
        resp = self.client.post(endpoint, json=_experiment_iteration_parameters)
        it8ar = Iter8AssessmentAndRecommendation(** resp.json())
        self.assertEqual(resp.status_code, 200, msg = "Successful request")

