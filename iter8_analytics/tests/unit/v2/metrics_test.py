"""Tests for iter8_analytics.api.v2.metrics_test"""
# standard python stuff
import logging
import re
from unittest import TestCase, mock

from iter8_analytics import fastapi_app
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants

from iter8_analytics.api.v2.metrics import get_params, get_url
from iter8_analytics.api.v2.types import ExperimentResource, MetricResource
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
        assert isinstance(err, KeyError)

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

def test_url_interpolation():
    """Test how parameters are computed"""
    expr = ExperimentResource(** er_example)
    metric_resource = expr.status.metrics[0].metricObj
    version = expr.spec.versionInfo.baseline
    start_time = expr.status.startTime
    params = get_params(metric_resource, version, start_time)
    groups = re.search('(\\[[0-9]+s\\])', params[0]["query"])
    assert groups is not None
