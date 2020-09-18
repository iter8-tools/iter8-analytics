"""Tests for module iter8_analytics.api.analytics.endpoints.metrics_test"""
# standard python stuff
import logging
from datetime import datetime, timezone
import json
import os
from pprint import pformat

# python libraries
import requests_mock
from fastapi import HTTPException
import numpy as np

# iter8 stuff
from iter8_analytics import fastapi_app
from iter8_analytics.api.types import *
import iter8_analytics.constants as constants
import iter8_analytics.config as config
from iter8_analytics.api.experiment import Experiment
from iter8_analytics.advancedparams import AdvancedParameters
from iter8_analytics.tests.unit.data.inputs.inputs import *

env_config = config.get_env_config()
logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'


class TestConvergence:
    def test_no_data(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_no_data_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            eip_eg = copy.deepcopy(eip_example)
            eip = ExperimentIterationParameters(** eip_eg)
            exp = Experiment(eip)
            for ind in range(10):
                resp = exp.run()
                if ind == 0:
                    initial_candidate_percent = resp.last_state['traffic_split_recommendation']['progressive']['reviews_candidate']
                eip.last_state = LastState(**resp.last_state)
                exp = Experiment(eip)
            assert resp.baseline_assessment.win_probability == 0.0
            assert resp.candidate_assessments[0].win_probability == 0.0
            assert resp.last_state['traffic_split_recommendation']['progressive']['reviews_candidate'] in [np.ceil(AdvancedParameters.exploration_traffic_percentage / (len(eip.candidates) + 1)), np.floor(AdvancedParameters.exploration_traffic_percentage / (len(eip.candidates) + 1))]
