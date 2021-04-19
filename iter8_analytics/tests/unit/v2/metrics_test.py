"""Tests for iter8_analytics.api.v2.metrics_test"""
# standard python stuff
import logging
import re
import os
import json
from unittest import TestCase, mock

# python libraries
import requests_mock

# external module dependencies
from requests.auth import HTTPBasicAuth

# iter8 dependencies
from iter8_analytics import fastapi_app
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants

from iter8_analytics.api.v2.metrics import get_params, get_url, get_headers, \
    get_basic_auth, get_body, get_metric_value
from iter8_analytics.api.v2.types import ExperimentResource, MetricInfo, \
    MetricResource, NamedValue, AuthType
from iter8_analytics.api.v2.examples.examples_canary import er_example
from iter8_analytics.api.v2.examples.examples_metrics import cpu_utilization

logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

logger.info(env_config)

class ParamInterpolation(TestCase):
    """Test parameter computation"""

    def test_params(self):
        """elapsedTime must not include 's' as suffix after parameter interpolation"""
        expr = ExperimentResource(** er_example)
        metric_resource = expr.status.metrics[0].metricObj
        version = expr.spec.versionInfo.baseline
        start_time = expr.status.startTime
        params = get_params(metric_resource, version, start_time)
        groups = re.search('(\\[[0-9]+s\\])', params[0]["query"])
        assert groups is not None

class URLTemplate(TestCase):
    """Test url interpolation"""

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_no_secret_ref(self, mock_secret):
        """When secret is None, url equals urlTemplate"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        url, _ = get_url(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert url == metric_resource.spec.urlTemplate

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_invalid_secret(self, mock_secret):
        """When secret is invalid, get error"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.secret = "invalid"
        mock_secret.return_value = ({}, \
            KeyError("cannot find secret invalid in namespace iter8-system"))
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url is None
        assert err is not None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_no_and_partialsecret_data(self, mock_secret):
        """When secret is valid, interpolate urlTemplate"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.urlTemplate = "https://prometheus.com:${port}/$endpoint"
        metric_resource.spec.secret = "valid"

        mock_secret.return_value = ({
            "port": 8080,
            "endpoint": "nothingtosee"
        }, None)
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:8080/nothingtosee"
        assert err is None

        mock_secret.return_value = ({
            "port": 8080
        }, None)
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:8080/$endpoint"
        assert err is None

        mock_secret.return_value = {}, None
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:${port}/$endpoint"
        assert err is None

        mock_secret.return_value = None, None
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:${port}/$endpoint"
        assert err is None

class HeaderTemplate(TestCase):
    """Test header computation"""

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_no_auth_type(self, mock_secret):
        """When authType is None, do not interpolate headers"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "a", value = "$b")
        ]
        headers, err = get_headers(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert headers == {
            "a": "$b"
        }
        assert err is None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_basic_auth_type(self, mock_secret):
        """When authType is Basic, do not interpolate headers"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "a", value = "$b")
        ]
        metric_resource.spec.authType = AuthType.BASIC
        headers, err = get_headers(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert headers == {
            "a": "$b"
        }
        assert err is None

        metric_resource.spec.secret = "valid"
        headers, err = get_headers(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert headers == {
            "a": "$b"
        }
        assert err is None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_invalid_secret(self, mock_secret):
        """When authType is APIKey or Bearer, and secret is invalid, get error"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "a", value = "$b")
        ]
        metric_resource.spec.secret = "invalid"
        mock_secret.return_value = ({}, \
            KeyError("cannot find secret invalid in namespace iter8-system"))

        metric_resource.spec.authType = AuthType.APIKEY
        headers, err = get_headers(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert headers is None
        assert err is not None

        metric_resource.spec.authType = AuthType.BEARER
        headers, err = get_headers(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert headers is None
        assert err is not None


    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_bearer_auth_type(self, mock_secret):
        """When authType is Bearer, and secret is valid, interpolate headers"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "Authorization", value = "Bearer $token")
        ]
        metric_resource.spec.authType = AuthType.BEARER
        metric_resource.spec.secret = "valid"
        mock_secret.return_value = ({
            "token": "t0p-secret"
        }, None)
        headers, err = get_headers(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert headers == {
            "Authorization": "Bearer t0p-secret"
        }
        assert err is None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_api_key_auth_type(self, mock_secret):
        """When authType is APIKey, and secret is valid, interpolate headers"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "a", value = "$b"),
            NamedValue(name = "c", value = "$d"),
            NamedValue(name = "e", value = "$f"),
            NamedValue(name = "g", value = "$h")
        ]
        metric_resource.spec.authType = AuthType.APIKEY
        metric_resource.spec.secret = "valid"
        mock_secret.return_value = ({
            "b": "b",
            "f": "f"
        }, None)
        headers, err = get_headers(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert headers == {
            "a": "b",
            "c": "$d",
            "e": "f",
            "g": "$h"
        }
        assert err is None

class BasicAuth(TestCase):
    """Test basic auth computation"""

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_basic_auth(self, mock_secret):
        """When authType is Basic, and secret is valid, get basic auth information"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.authType = AuthType.BASIC
        metric_resource.spec.secret = "valid"
        mock_secret.return_value = ({
            "username": "me",
            "password": "t0p-secret"
        }, None)
        auth, err = get_basic_auth(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert auth == HTTPBasicAuth("me", "t0p-secret")
        assert err is None

        with requests_mock.mock(real_http=True) as req_mock:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                        'prometheus_sample_response.json')
            response_json = json.load(open(file_path))
            req_mock.get(metric_resource.spec.urlTemplate, json=response_json)

            version = expr.spec.versionInfo.baseline
            start_time = expr.status.startTime
            value, err = get_metric_value(metric_resource, version, start_time)
            assert err is None
            assert value == float(response_json["data"]["result"][0]["value"][1])

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_basic_auth_invalid(self, mock_secret):
        """When authType is Basic, and secret is invalid, get error"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.authType = AuthType.BASIC

        auth, err = get_basic_auth(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert auth is None
        assert err is not None

        metric_resource.spec.secret = "invalid"
        mock_secret.return_value = ({}, \
            KeyError("cannot find secret invalid in namespace iter8-system"))
        auth, err = get_basic_auth(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert auth is None
        assert err is not None

        mock_secret.return_value = ({
            "username": "me"
        }, None)
        auth, err = get_basic_auth(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert auth is None
        assert err is not None

class BodyInterpolation(TestCase):
    """Test body computation"""

    def test_body(self):
        """body must interpolate elapsedTime and version name"""
        expr = ExperimentResource(** er_example)
        metric_info = MetricInfo(** cpu_utilization)
        version = expr.spec.versionInfo.baseline
        start_time = expr.status.startTime
        body, err = get_body(metric_info.metricObj, version, start_time)
        assert err is None
        assert body["last"]  > 32931645
        assert body["filter"] == "kubernetes.node.name = 'n1' and service = 'default'"

    def test_POST_metric(self):
        """POST metric query must result in a value"""
        with requests_mock.mock(real_http=True) as req_mock:
            req_mock.register_uri('POST', cpu_utilization["metricObj"]
                                  ["spec"]["urlTemplate"], json={
                                      "data": [
                                          {
                                              "t": 1582756200,
                                              "d": [
                                                  6.481
                                              ]
                                          }
                                      ],
                "start": 1582755600,
                "end": 1582756200
            }, status_code=200)

            expr = ExperimentResource(** er_example)
            metric_info = MetricInfo(** cpu_utilization)
            version = expr.spec.versionInfo.baseline
            start_time = expr.status.startTime
            value, err = get_metric_value(metric_info.metricObj, version, start_time)
            assert err is None
            assert value == 6.481




