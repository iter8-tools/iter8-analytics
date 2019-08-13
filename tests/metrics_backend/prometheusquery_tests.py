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
from iter8_analytics.metrics_backend.prometheusquery import PrometheusQuery
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
        #flask_app.initialize(flask_app.app)

        # Get an internal Flask test client
        cls.flask_test = flask_app.app.test_client()

        cls.backend_url = os.getenv(constants.ITER8_ANALYTICS_METRICS_BACKEND_URL_ENV)
        cls.metrics_endpoint = f'{cls.backend_url}/api/v1/query'
        cls.endpoint = f'http://localhost:5555/api/v1/analytics/canary/check_and_increment'
        log.info('Completed initialization for all analytics REST API tests.')


    def test_prometheus_responses(self):
        #No value for Correctness query
        query_spec = {
        "query_name": "value",
        "query_template": "query_template",
        "metric_type": "Correctness",
        "entity_tags": "entity_tags"
        }
        prometheus_object = PrometheusQuery("http://localhost:9090", query_spec)

        result = prometheus_object.post_process({"status": "success", "data": {"resultType": "vector", "result": []}})
        self.assertEqual(result["message"], "No data found in Prometheus but query succeeded. Return value based on metric type")
        self.assertEqual(result["value"], 0)

        #No value for Performance query
        query_spec = {
        "query_name": "value",
        "query_template": "query_template",
        "metric_type": "Performance",
        "entity_tags": "entity_tags"
        }
        prometheus_object = PrometheusQuery("http://localhost:9090", query_spec)

        result = prometheus_object.post_process({"status": "success", "data": {"resultType": "vector", "result": []}})
        self.assertEqual(result["message"], "No data found in Prometheus but query succeeded. Return value based on metric type")
        self.assertEqual(result["value"], None)
