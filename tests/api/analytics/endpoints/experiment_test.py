"""Tests for module iter8_analytics.api.analytics.endpoints.metrics_test"""
# standard python stuff
import logging
from datetime import datetime
import json

# python libraries
import requests_mock

# iter8 stuff
from iter8_analytics import fastapi_app
from iter8_analytics.api.analytics.types import *
import iter8_analytics.constants as constants
import iter8_analytics.config as config
from iter8_analytics.api.analytics.experiment import Experiment
from iter8_analytics.api.analytics.endpoints.examples import *

env_config = config.get_env_config()
fastapi_app.config_logger(env_config[constants.LOG_LEVEL])
logger = logging.getLogger('iter8_analytics')

metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'

class TestExperiment:
    def test_experiment_object_initialization(self):
        eip = ExperimentIterationParameters(** eip_example)
        exp = Experiment(eip)

        eip_with_last_state = ExperimentIterationParameters(** reviews_example_with_last_state)
        exp_with_last_state = Experiment(eip_with_last_state)

        eip_with_partial_last_state = ExperimentIterationParameters(** reviews_example_with_partial_last_state)
        exp_with_partial_last_state = Experiment(eip_with_partial_last_state)

        eip_with_ratio_max_mins = ExperimentIterationParameters(** reviews_example_with_ratio_max_mins)
        exp_with_partial_last_state = Experiment(eip_with_ratio_max_mins)

    def test_invalid_ratio_metric(self):
        try:
            eip = ExperimentIterationParameters(** eip_with_invalid_ratio)
            exp = Experiment(eip)
        except KeyError as ke:
            pass

    def test_unknown_metric_in_criterion(self):
        try:
            eip = ExperimentIterationParameters(** eip_with_unknown_metric_in_criterion)
            exp = Experiment(eip)
        except KeyError as ke:
            pass

    def test_get_ratio_max_min(self):
        with requests_mock.mock(real_http=True) as m:
            m.get(metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            eip = ExperimentIterationParameters(** eip_example)
            exp = Experiment(eip)
            exp.run()

            eip = ExperimentIterationParameters(** reviews_example_with_last_state)
            exp = Experiment(eip)
            exp.run()

            eip = ExperimentIterationParameters(** reviews_example_with_partial_last_state)
            exp = Experiment(eip)
            exp.run()

            eip = ExperimentIterationParameters(** reviews_example_with_ratio_max_mins)
            exp = Experiment(eip)
            exp.run()

    def test_missing_iter8_request_count(self):
        with requests_mock.mock(real_http=True) as m:
            m.get(metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            eip = ExperimentIterationParameters(** reviews_example_without_request_count)
            exp = Experiment(eip)
            resp = exp.run()

            assert resp.baseline_assessment.request_count is None
            for assessment in resp.candidate_assessments:
                assert assessment.request_count is None

class TestDetailedVersion:
    def test_detailed_version(self):
        eip_with_ratio_max_mins = ExperimentIterationParameters(** reviews_example_with_ratio_max_mins)
        exp_with_partial_last_state = Experiment(eip_with_ratio_max_mins)

        exp_with_partial_last_state.detailed_versions['reviews_candidate'].aggregate_ratio_metrics({
            "iter8_mean_latency": AggregatedRatioDataPoint(
                value = 20.0, timestamp = datetime.now(), status = StatusEnum.all_ok)
        })

    def test_create_assessment(self):
        eip_with_ratio_max_mins = ExperimentIterationParameters(** reviews_example_with_ratio_max_mins)
        exp_with_partial_last_state = Experiment(eip_with_ratio_max_mins)

        exp_with_partial_last_state.detailed_versions['reviews_candidate'].aggregate_ratio_metrics({
            "iter8_mean_latency": AggregatedRatioDataPoint(
                value = 20.0, timestamp = datetime.now(), status = StatusEnum.all_ok)
        })

        exp_with_partial_last_state.detailed_versions['reviews_candidate'].create_assessment()