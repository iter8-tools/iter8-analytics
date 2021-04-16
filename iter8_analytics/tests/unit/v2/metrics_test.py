"""Tests for iter8_analytics.api.v2.metrics_test"""
# standard python stuff
import logging
import re
from unittest import TestCase, mock

from iter8_analytics import fastapi_app
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants

from iter8_analytics.api.v2.metrics import get_params, get_url, get_headers
from iter8_analytics.api.v2.types import ExperimentResource, MetricResource, \
    NamedValue, AuthType
from iter8_analytics.api.v2.examples.examples_canary import er_example

logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

logger.info(env_config)

def test_params():
    """Test how parameters are computed"""
    expr = ExperimentResource(** er_example)
    metric_resource = expr.status.metrics[0].metricObj
    version = expr.spec.versionInfo.baseline
    start_time = expr.status.startTime
    params = get_params(metric_resource, version, start_time)
    groups = re.search('(\\[[0-9]+s\\])', params[0]["query"])
    assert groups is not None


class URLTemplateTestCases(TestCase):
    """Tests following behaviors during interpolation of URLTemplate.
    1. urlTemplate interpolation: not attempted when secret is not referenced; url == urlTemplate
    2. urlTemplate interpolation: exception when secret is invalid
    3. urlTemplate interpolation: interpolated with data when data has placeholder values
    4. urlTemplate interpolation: url == urlTemplate,
    when data is None or does not have the placeholder values
    """

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_no_secret_ref(self, mock_secret):
        """When there is no secret reference in the metric, url should equal urlTemplate"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        url, _ = get_url(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert url == metric_resource.spec.urlTemplate

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_invalid_secret(self, mock_secret):
        """When there is no secret reference in the metric, url should equal urlTemplate"""
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
    def test_valid_secret(self, mock_secret):
        """When there is a valid secret reference in the metric, 
        placeholders in the urlTemplate must be substituted correctly"""
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

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_no_and_partialsecret_data(self, mock_secret):
        """When there is a valid secret reference in the metric, 
        placeholders in the urlTemplate must be substituted correctly"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.urlTemplate = "https://prometheus.com:${port}/$endpoint"
        metric_resource.spec.secret = "valid"

        mock_secret.return_value = ({
            "port": 8080
        }, None)
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:8080/$endpoint"
        assert err is None

        mock_secret.return_value = None, None
        (url, err) = get_url(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert url == "https://prometheus.com:${port}/$endpoint"
        assert err is None

class HeaderTemplateTestCases(TestCase):
    """Tests following behaviors during computation of headers.
    1. When authType is None, do not interpolate headers
    2. When authType is Basic, do not interpolate headers
    """

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
    def test_non_api_keys_auth_type(self, mock_secret):
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

        metric_resource.spec.authType = AuthType.BEARER
        headers, err = get_headers(metric_resource)
        self.assertFalse(mock_secret.called, \
            "attempt to fetch secret when no secret is referenced in metric resource")
        assert headers == {
            "a": "$b"
        }
        assert err is None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_invalid_secret(self, mock_secret):
        """When authType is absent in the metric resource, do not interpolate headers"""
        expr = ExperimentResource(** er_example)
        metric_resource: MetricResource = expr.status.metrics[0].metricObj
        metric_resource.spec.headerTemplates = [
            NamedValue(name = "a", value = "$b")
        ]
        metric_resource.spec.authType = AuthType.APIKEY
        metric_resource.spec.secret = "invalid"
        mock_secret.return_value = ({}, \
            KeyError("cannot find secret invalid in namespace iter8-system"))
        headers, err = get_headers(metric_resource)
        mock_secret.assert_called_with(metric_resource)
        assert headers is None
        assert err is not None

    @mock.patch('iter8_analytics.api.v2.metrics.get_secret_data_for_metric')
    def test_api_key_auth_type(self, mock_secret):
        """When authType is APIKey, interpolate headers"""
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

def test_url_interpolation():
    """Test how parameters are computed"""
    expr = ExperimentResource(** er_example)
    metric_resource = expr.status.metrics[0].metricObj
    version = expr.spec.versionInfo.baseline
    start_time = expr.status.startTime
    params = get_params(metric_resource, version, start_time)
    groups = re.search('(\\[[0-9]+s\\])', params[0]["query"])
    assert groups is not None
