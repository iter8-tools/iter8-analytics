"""Tests for module iter8_analytics.api.analytics.endpoints.metrics"""
# standard python stuff
import logging
import requests_mock
import json

# iter8 stuff
from iter8_analytics import fastapi_app
from iter8_analytics.api.types import *
import iter8_analytics.constants as constants
import iter8_analytics.config as config
from iter8_analytics.api.detailedmetric import *
from iter8_analytics.tests.unit.data.inputs.inputs import *
from iter8_analytics.api.detailedversion import *
from iter8_analytics.api.experiment import *

env_config = config.get_env_config()
logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'


class TestDetailedMetrics:
    def test_non_zero_to_one_belief_update(self):
        eip = ExperimentIterationParameters(** eip_with_percentile)
        exp = Experiment(eip)
        dv = DetailedCandidateVersion(eip.candidates[0], exp, 2.0)
        rm = DetailedRatioMetric(eip.metric_specs.ratio_metrics[0], dv)

        exp.ratio_max_mins = {
            rm.metric_id: RatioMaxMin(minimum=5.7, maximum=8.9)
        }

        rm.aggregated_metric = AggregatedRatioDataPoint(
            value=6.2, timestamp=datetime.now(timezone.utc))

        denominator_id = rm.metric_spec.denominator
        rm.detailed_version.metrics["counter_metrics"][denominator_id] = DetailedCounterMetric(
            eip.metric_specs.ratio_metrics[0], dv)
        rm.detailed_version.metrics["counter_metrics"][denominator_id].aggregated_metric = AggregatedCounterDataPoint(
            value=6.3, timestamp=datetime.now(timezone.utc))
        rm.update_belief()

    def test_bad_zero_to_one_belief_update(self):
        bad_eip = copy.deepcopy(eip_with_percentile)
        bad_eip["metric_specs"]["ratio_metrics"][0]["zero_to_one"] = True

        eip = ExperimentIterationParameters(** bad_eip)

        exp = Experiment(eip)
        dv = DetailedCandidateVersion(eip.candidates[0], exp, 2.0)
        rm = DetailedRatioMetric(eip.metric_specs.ratio_metrics[0], dv)

        exp.ratio_max_mins = {
            rm.metric_id: RatioMaxMin(minimum=5.7, maximum=8.9)
        }

        rm.aggregated_metric = AggregatedRatioDataPoint(
            value=6.2, timestamp=datetime.now(timezone.utc))

        denominator_id = rm.metric_spec.denominator
        rm.detailed_version.metrics["counter_metrics"][denominator_id] = DetailedCounterMetric(
            eip.metric_specs.ratio_metrics[0], dv)
        rm.detailed_version.metrics["counter_metrics"][denominator_id].aggregated_metric = AggregatedCounterDataPoint(
            value=6.3, timestamp=datetime.now(timezone.utc))

        try:
            rm.update_belief()
        except HTTPException as e:
            pass

    def test_good_zero_to_one_belief_update(self):
        eip = ExperimentIterationParameters(** eip_with_percentile)

        exp = Experiment(eip)
        dv = DetailedCandidateVersion(eip.candidates[0], exp, 2.0)
        rm = DetailedRatioMetric(eip.metric_specs.ratio_metrics[3], dv)

        exp.ratio_max_mins = {
            rm.metric_id: RatioMaxMin(minimum=0.3, maximum=1.0)
        }

        rm.aggregated_metric = AggregatedRatioDataPoint(
            value=0.993, timestamp=datetime.now(timezone.utc))

        denominator_id = rm.metric_spec.denominator
        rm.detailed_version.metrics["counter_metrics"][denominator_id] = DetailedCounterMetric(
            eip.metric_specs.ratio_metrics[0], dv)
        rm.detailed_version.metrics["counter_metrics"][denominator_id].aggregated_metric = AggregatedCounterDataPoint(
            value=13, timestamp=datetime.now(timezone.utc))

        rm.update_belief()
