"""Tests for module iter8_analytics.api.analytics.endpoints.metrics_test"""
# standard python stuff
import logging
import json
import os
import copy

# python libraries
import requests_mock
from fastapi import HTTPException


from iter8_analytics import fastapi_app
from iter8_analytics.api.v2.types import *
from iter8_analytics.config import env_config
import iter8_analytics.constants as constants
from iter8_analytics.tests.unit.v2.data.inputs.inputs import *

from iter8_analytics.api.v2.metrics import get_aggregated_metrics
from iter8_analytics.api.v2.experiment import get_version_assessments, get_winner_assessment, \
     get_weights, get_analytics_results


logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

prometheus_url_template = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{prometheus_url_template}/api/v1/query'


class TestExperiment:
    def test_v2_input_object(self):
        er = ExperimentResource(** er_example)
        er = ExperimentResource(** er_example_step1)
        er = ExperimentResource(** er_example_step2)
        er = ExperimentResource(** er_example_step3)
        
        
    def test_experiment_response_objects(self):
        am = AggregatedMetric(** am_response)
        va = VersionAssessments(** va_response)
        wa = WinnerAssessment(** wa_response)
        w = Weights(** w_response)

    def test_v2_aggregated_metrics_endpoint(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            er = ExperimentResource(** er_example)
            get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
        
    def test_v2_version_assessment_endpoint(self):
        er = ExperimentResource(** er_example_step1)
        get_version_assessments(er.convert_to_float())
    
    def test_v2_winner_assessment_endpoint(self):
        er = ExperimentResource(** er_example_step2)
        get_winner_assessment(er.convert_to_float())
    
    def test_v2_weights_endpoint(self):
        er = ExperimentResource(** er_example_step3)
        get_weights(er.convert_to_float())
    
    def test_v2_va_without_am(self):
        er = ExperimentResource(** er_example)
        try:
            get_version_assessments(er.convert_to_float())
        except AttributeError:
            pass

    def test_v2_wa_without_va(self):
        er = ExperimentResource(** er_example)
        try:
            get_winner_assessment(er.convert_to_float())
        except AttributeError:
            pass
    
    def test_v2_w_without_wa(self):
        er = ExperimentResource(** er_example)
        try:
            get_weights(er.convert_to_float())
        except AttributeError:
            pass
    
    def test_v2_va_without_mean_latency_metric(self):
        eg = copy.deepcopy(er_example_step1)
        eg['status']['analysis']['aggregatedMetrics']["data"].pop('mean-latency', None)
        er = ExperimentResource(** eg)
        resp = get_version_assessments(er.convert_to_float())
        assert(resp.message == "Error: ; Warning: Aggregated metric object for mean-latency metric is unavailable.; Info: ")

    def test_v2_canary_passing_criteria(self):
        eg = copy.deepcopy(er_example_step1)
        eg['spec']['criteria']['objectives'][0]['upperLimit'] = 500
        er = ExperimentResource(** eg)
        resp = get_version_assessments(er.convert_to_float())
        assert(resp.data == {'default': [True], 'canary': [True]})

    def test_v2_canary_failing_criteria(self):
        er = ExperimentResource(** er_example_step1)
        resp = get_version_assessments(er.convert_to_float())
        assert(resp.data == {'default': [True], 'canary': [False]})

    def test_v2_canary_is_winner(self):
        eg = copy.deepcopy(er_example_step2)

        eg['status']['analysis']['versionAssessments'] = {
            "data": {
                "default": [
                    True
                ],
                "canary": [
                    True
                ]
            },
            "message": "All ok"
        }
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())
        assert(resp.data.winnerFound == wa_response['data']['winnerFound'])
        assert(resp.data.winner == wa_response['data']['winner'])

    def test_v2_default_is_winner(self):
        eg = copy.deepcopy(er_example_step2)

        eg['status']['analysis']['versionAssessments'] = {
            "data": {
                "default": [
                    True
                ],
                "canary": [
                    False
                ]
            },
            "message": "All ok"
        }
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())

        assert(resp.data.winnerFound == wa_response['data']['winnerFound'])
        assert(resp.data.winner == 'default')
    
    def test_v2_no_winner(self):
        eg = copy.deepcopy(er_example_step2)

        eg['status']['analysis']['versionAssessments'] = {
            "data": {
                "default": [
                    False
                ],
                "canary": [
                    False
                ]
            },
            "message": "All ok"
        }
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())

        assert(resp.data.winnerFound == False)