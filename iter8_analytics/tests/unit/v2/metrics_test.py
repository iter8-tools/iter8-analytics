"""Tests for iter8_analytics.api.v2.metrics_test"""
# standard python stuff
import logging
import re

from iter8_analytics import fastapi_app
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants

from iter8_analytics.api.v2.metrics import get_params
from iter8_analytics.api.v2.types import ExperimentResource
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
