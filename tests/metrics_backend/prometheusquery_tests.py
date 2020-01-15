"""Tests for the PrometheusQuery Class."""

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
    def test_prometheus_responses(self):
        #No value for Correctness query
        query_spec = {
        "query_name": "value",
        "query_template": "query_template",
        "is_counter": True,
        "absent_value": "0.0",
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
        "is_counter": False,
        "absent_value": "None",
        "entity_tags": "entity_tags"
        }
        prometheus_object = PrometheusQuery("http://localhost:9090", query_spec)

        result = prometheus_object.post_process({"status": "success", "data": {"resultType": "vector", "result": []}})
        self.assertEqual(result["message"], "No data found in Prometheus but query succeeded. Return value based on metric type")
        self.assertEqual(result["value"], None)
