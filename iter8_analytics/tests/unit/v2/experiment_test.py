"""Tests for module iter8_analytics.api.v2"""
# standard python stuff
import logging
import json
import os
import copy

# python libraries
import requests_mock
from fastapi import HTTPException

from iter8_analytics import fastapi_app
from iter8_analytics.api.v2.types import \
    ExperimentResource, AggregatedMetricsAnalysis, VersionAssessmentsAnalysis, \
        WinnerAssessmentAnalysis, WeightsAnalysis
from iter8_analytics.config import env_config, unmarshal
import iter8_analytics.constants as constants
# from iter8_analytics.tests.unit.v2.data.inputs.inputs import \
#     er_example, er_example_step1, er_example_step2, er_example_step3, \
#         am_response, va_response, wa_response, w_response

# from iter8_analytics.tests.unit.v2.data.inputs.inputs_ab import \
#     ab_er_example, ab_er_example_step1, ab_er_example_step2, ab_er_example_step3, \
#         ab_am_response, ab_va_response, ab_wa_response, ab_w_response

from iter8_analytics.tests.unit.v2.data.inputs.inputs_abn import \
    abn_er_example, abn_er_example_step1, abn_er_example_step2, abn_er_example_step3, \
        abn_am_response, abn_va_response, abn_wa_response, abn_w_response

from iter8_analytics.api.v2.metrics import get_aggregated_metrics
from iter8_analytics.api.v2.experiment import get_version_assessments, get_winner_assessment, \
     get_weights, get_analytics_results


logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

logger.info(env_config)
logger.info(unmarshal)


class TestExperiment:
    """Test Iter8 v2 experiment, metrics and types"""
    # def test_v2_input_object(self):
    #     ExperimentResource(** er_example)
    #     ExperimentResource(** er_example_step1)
    #     ExperimentResource(** er_example_step2)
    #     ExperimentResource(** er_example_step3)
        
        
    # def test_experiment_response_objects(self):
    #     AggregatedMetricsAnalysis(** am_response)
    #     VersionAssessmentsAnalysis(** va_response)
    #     WinnerAssessmentAnalysis(** wa_response)
    #     WeightsAnalysis(** w_response)

    # def test_v2_aggregated_metrics_endpoint(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         response_json = json.load(open(file_path))
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=response_json)

    #         expr = ExperimentResource(** er_example)
    #         agm = get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()
    #         logger.info(agm)
    #         assert(agm.data['request-count'].data['default'].value == response_json['data']['result'][0]['value'][1])
        
    # def test_v2_version_assessment_endpoint(self):
    #     er = ExperimentResource(** er_example_step1)
    #     get_version_assessments(er.convert_to_float())
    
    # def test_v2_winner_assessment_endpoint(self):
    #     er = ExperimentResource(** er_example_step2)
    #     get_winner_assessment(er.convert_to_float())
    
    # def test_v2_weights_endpoint(self):
    #     er = ExperimentResource(** er_example_step3)
    #     get_weights(er.convert_to_float())
    
    # def test_v2_analytics_assessment_endpoint(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))

    #         er = ExperimentResource(** er_example)
    #         get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_am_without_candidates(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         er = ExperimentResource(** eg)
    #         get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_am_incorrect_tag_names(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(er_example)
    #         eg['spec']['metrics'][0]['metricObj']['spec']['params'][0]['value'] = "sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0)"
    #         eg['spec']['metrics'][1]['metricObj']['spec']['params'][0]['value'] = "(sum(increase(revision_app_request_latencies_sum{revision_name=~'.*$svc_name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0))"
    #         eg['spec']['versionInfo']['baseline']['variables'] = [{"name": "revision_name", "value": "sample-application-v1"}]
    #         eg['spec']['versionInfo']['candidates'][0]['variables'] = [{"name": "revision_name", "value": "sample-application-v2"}]
    #         er = ExperimentResource(** eg)
            
    #         resp = get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    #         logger.info(resp)
    #         assert("Error from metrics backend for metric" in resp.message)
    
    # def test_v2_analytics_assessment_conformance(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
    #         eg = copy.deepcopy(er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         eg['spec']['strategy']['testingPattern'] = 'Conformance'
    #         er = ExperimentResource(** eg)
    #         get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_version_assessment_conformance(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
    #         eg = copy.deepcopy(er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         eg['spec']['strategy']['testingPattern'] = 'Conformance'
    #         er = ExperimentResource(** eg)
    #         resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
    #         assert(resp.versionAssessments.data == {'default': [True]})

    # def test_v2_va_without_am(self):
    #     er = ExperimentResource(** er_example)
    #     try:
    #         get_version_assessments(er.convert_to_float())
    #     except AttributeError:
    #         pass

    # def test_v2_wa_without_va(self):
    #     er = ExperimentResource(** er_example)
    #     try:
    #         get_winner_assessment(er.convert_to_float())
    #     except AttributeError:
    #         pass
    
    # def test_v2_w_without_wa(self):
    #     er = ExperimentResource(** er_example)
    #     try:
    #         get_weights(er.convert_to_float())
    #     except AttributeError:
    #         pass

    # def test_v2_no_prometheus_response(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_no_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))

    #         er = ExperimentResource(** er_example)
    #         resp = get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    #         expected_response = {
    #                 "request-count": {
    #                     "max": None,
    #                     "min": None,
    #                     "data": {
    #                         "default": {
    #                             "max": None,
    #                             "min": None,
    #                             "sampleSize": None,
    #                             "value": None
    #                         },
    #                         "canary": {
    #                             "max": None,
    #                             "min": None,
    #                             "sampleSize": None,
    #                             "value": None
    #                         }
    #                     }
    #                 },
    #                 "mean-latency": {
    #                     "max": None,
    #                     "min": None,
    #                     "data": {
    #                         "default": {
    #                             "max": None,
    #                             "min": None,
    #                             "sampleSize": None,
    #                             "value": None
    #                         },
    #                         "canary": {
    #                             "max": None,
    #                             "min": None,
    #                             "sampleSize": None,
    #                             "value": None
    #                         }
    #                     }
    #                 }
    #             }
    #         assert(resp.data == expected_response)
    
    # def test_v2_va_with_no_metric_value(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_no_response.json')
    #         m.get(er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))

    #         er = ExperimentResource(** er_example)
    #         resp = get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()

    #         eg = copy.deepcopy(er_example_step1)
    #         eg['status']['analysis']["aggregatedMetrics"] = resp
    #         er = ExperimentResource(** eg)
    #         resp2 = get_version_assessments(er.convert_to_float())
            
    #         assert(resp2.data == {'default': [False], 'canary': [False]})
                
    # def test_v2_va_without_mean_latency_metric(self):
    #     eg = copy.deepcopy(er_example_step1)
    #     eg['status']['analysis']['aggregatedMetrics']["data"].pop('mean-latency', None)
    #     er = ExperimentResource(** eg)
    #     resp = get_version_assessments(er.convert_to_float())
    #     assert(resp.message == "Error: ; Warning: Aggregated metric object for mean-latency metric is unavailable.; Info: ")

    # def test_v2_canary_passing_criteria(self):
    #     eg = copy.deepcopy(er_example_step1)
    #     eg['spec']['criteria']['objectives'][0]['upperLimit'] = 500
    #     er = ExperimentResource(** eg)
    #     resp = get_version_assessments(er.convert_to_float())
    #     assert(resp.data == {'default': [True], 'canary': [True]})

    # def test_v2_canary_failing_upperlimit_criteria(self):
    #     er = ExperimentResource(** er_example_step1)
    #     resp = get_version_assessments(er.convert_to_float())
    #     assert(resp.data == {'default': [True], 'canary': [False]})
    
    # def test_v2_canary_failing_lowerlimit_criteria(self):
    #     eg = copy.deepcopy(er_example_step1)
    #     eg['spec']['criteria']['objectives'][0].pop('upperLimit')
    #     eg['spec']['criteria']['objectives'][0]['lowerLimit'] = 500
    #     er = ExperimentResource(** eg)
    #     resp = get_version_assessments(er.convert_to_float())
    #     assert(resp.data == {'default': [False], 'canary': [False]})
    
    # def test_v2_canary_is_winner(self):
    #     eg = copy.deepcopy(er_example_step2)

    #     eg['status']['analysis']['versionAssessments'] = {
    #         "data": {
    #             "default": [
    #                 True
    #             ],
    #             "canary": [
    #                 True
    #             ]
    #         },
    #         "message": "All ok"
    #     }
    #     er = ExperimentResource(** eg)
    #     resp = get_winner_assessment(er.convert_to_float())
    #     assert(resp.data.winnerFound == wa_response['data']['winnerFound'])
    #     assert(resp.data.winner == wa_response['data']['winner'])

    # def test_v2_analytics_assessment_conformance_winner(self):
    #         eg = copy.deepcopy(er_example_step2)

    #         eg['status']['analysis']['versionAssessments'] = {
    #             "data": {
    #                 "default": [
    #                     True
    #                 ]
    #             },
    #             "message": "All ok"
    #         }
    #         del(eg['spec']['versionInfo']['candidates'])
    #         eg['spec']['strategy']['testingPattern'] = 'Conformance'
    #         er = ExperimentResource(** eg)
    #         resp = get_winner_assessment(er.convert_to_float())
    #         assert(resp.data.winnerFound == True)
    #         assert(resp.data.winner == 'default')

    # def test_v2_default_is_winner(self):
    #     eg = copy.deepcopy(er_example_step2)

    #     eg['status']['analysis']['versionAssessments'] = {
    #         "data": {
    #             "default": [
    #                 True
    #             ],
    #             "canary": [
    #                 False
    #             ]
    #         },
    #         "message": "All ok"
    #     }
    #     er = ExperimentResource(** eg)
    #     resp = get_winner_assessment(er.convert_to_float())

    #     assert(resp.data.winnerFound == wa_response['data']['winnerFound'])
    #     assert(resp.data.winner == 'default')
    
    # def test_v2_no_winner(self):
    #     eg = copy.deepcopy(er_example_step2)

    #     eg['status']['analysis']['versionAssessments'] = {
    #         "data": {
    #             "default": [
    #                 False
    #             ],
    #             "canary": [
    #                 False
    #             ]
    #         },
    #         "message": "All ok"
    #     }
    #     er = ExperimentResource(** eg)
    #     resp = get_winner_assessment(er.convert_to_float())

    #     assert(resp.data.winnerFound == False)
    
    # def test_v2_weights_with_winner(self):
    #     er = ExperimentResource(** er_example_step3)
    #     resp = get_weights(er.convert_to_float())  

    #     expected_resp = [{
    #             "name": "default",
    #             "value": 5

    #         },{
    #             "name": "canary",
    #             "value": 95

    #         }]      
    #     assert(resp.data == expected_resp)

    # def test_v2_weights_with_no_winner(self):
    #     eg = copy.deepcopy(er_example_step3)
    #     eg['status']['analysis']['winnerAssessment']['data'] = {
    #         "winnerFound": False
    #     }
    #     er = ExperimentResource(** eg)
    #     resp = get_weights(er.convert_to_float()) 
    #     assert(resp.data == w_response['data'])
    
    # def test_v2_inc_old_weights_and_best_versions_and_canary_winner(self):
    #     eg = copy.deepcopy(er_example_step3)
    #     eg['status']['currentWeightDistribution'] = [{
    #             "name": "default",
    #             "value": 70

    #         },{
    #             "name": "canary",
    #             "value": 30

    #         }]
    #     expected_resp = [{
    #             "name": "default",
    #             "value": 5

    #         },{
    #             "name": "canary",
    #             "value": 95

    #         }]
    #     er = ExperimentResource(** eg)
    #     resp = get_weights(er.convert_to_float())         
    #     assert(resp.data == expected_resp)

    # def test_v2_inc_old_weights_and_no_best_versions(self):
    #     eg = copy.deepcopy(er_example_step3)
    #     eg['status']['currentWeightDistribution'] = [{
    #             "name": "default",
    #             "value": 50

    #         },{
    #             "name": "canary",
    #             "value": 50

    #         }]
    #     eg["status"]["analysis"]["winnerAssessment"]["data"] = {
    #         "winnerFound": False
    #     } 
    #     expected_resp = [{
    #             "name": "default",
    #             "value": 95

    #         },{
    #             "name": "canary",
    #             "value": 5

    #         }]
    #     er = ExperimentResource(** eg)
    #     resp = get_weights(er.convert_to_float())
    #     assert(resp.data == expected_resp)
    
    # def test_v2_set_weights_config(self):
    #     eg = copy.deepcopy(er_example_step3)
    #     eg['status']['currentWeightDistribution'] = [{
    #             "name": "default",
    #             "value": 50

    #         },{
    #             "name": "canary",
    #             "value": 50

    #         }]

    #     eg['spec']['strategy']['weights'] = {
    #         "maxCandidateWeight": 53,
    #         "maxCandidateWeightIncrement": 2,
    #         "algorithm": 'Progressive'
    #     }

    #     expected_resp = [{
    #             "name": "default",
    #             "value": 48

    #         },{
    #             "name": "canary",
    #             "value": 52

    #         }]
    #     er = ExperimentResource(** eg)
    #     resp = get_weights(er.convert_to_float())
    #     assert(resp.data == expected_resp)
    
    # ########## A/B TESTS #############
    # def test_v2_ab_input_object(self):
    #     ExperimentResource(** ab_er_example)
    #     ExperimentResource(** ab_er_example_step1)
    #     ExperimentResource(** ab_er_example_step2)
    #     ExperimentResource(** ab_er_example_step3)
        
        
    # def test_experiment_ab_response_objects(self):
    #     AggregatedMetricsAnalysis(** ab_am_response)
    #     VersionAssessmentsAnalysis(** ab_va_response)
    #     WinnerAssessmentAnalysis(** ab_wa_response)
    #     WeightsAnalysis(** ab_w_response)

    # def test_v2_ab_aggregated_metrics_endpoint(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         response_json = json.load(open(file_path))
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=response_json)

    #         expr = ExperimentResource(** ab_er_example)
    #         agm = get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()
    #         assert(agm.data['request-count'].data['default'].value == response_json['data']['result'][0]['value'][1])
        
    # def test_v2_ab_version_assessment_endpoint(self):
    #     er = ExperimentResource(** ab_er_example_step1)
    #     get_version_assessments(er.convert_to_float())
    
    # def test_v2_ab_winner_assessment_endpoint(self):
    #     er = ExperimentResource(** ab_er_example_step2)
    #     get_winner_assessment(er.convert_to_float())
    
    # def test_v2_ab_weights_endpoint(self):
    #     er = ExperimentResource(** ab_er_example_step3)
    #     get_weights(er.convert_to_float())
    
    # def test_v2_ab_analytics_assessment_endpoint(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))

    #         er = ExperimentResource(** ab_er_example)
    #         get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_ab_am_without_candidates(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(ab_er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         er = ExperimentResource(** eg)
    #         get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_ab_am_incorrect_tag_names(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(ab_er_example)
    #         eg['spec']['metrics'][0]['metricObj']['spec']['params'][0]['value'] = "sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0)"
    #         eg['spec']['metrics'][1]['metricObj']['spec']['params'][0]['value'] = "(sum(increase(revision_app_request_latencies_sum{revision_name=~'.*$svc_name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0))"
    #         eg['spec']['versionInfo']['baseline']['variables'] = [{"name": "revision_name", "value": "sample-application-v1"}]
    #         eg['spec']['versionInfo']['candidates'][0]['variables'] = [{"name": "revision_name", "value": "sample-application-v2"}]
    #         er = ExperimentResource(** eg)
            
    #         resp = get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    #         assert("Error from metrics backend for metric" in resp.message)
    
    # def test_v2_ab_analytics_assessment_conformance(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
    #         eg = copy.deepcopy(ab_er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         eg['spec']['strategy']['testingPattern'] = 'Conformance'
    #         er = ExperimentResource(** eg)
    #         get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    # def test_v2_ab_version_assessment_conformance(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
    #         eg = copy.deepcopy(ab_er_example)
    #         del(eg['spec']['versionInfo']['candidates'])
    #         eg['spec']['strategy']['testingPattern'] = 'Conformance'
    #         er = ExperimentResource(** eg)
    #         resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
    #         assert(resp.versionAssessments.data == {'default': [True]})

    # def test_v2_ab_va_without_am(self):
    #     er = ExperimentResource(** ab_er_example)
    #     try:
    #         get_version_assessments(er.convert_to_float())
    #     except AttributeError:
    #         pass

    # def test_v2_ab_wa_without_va(self):
    #     er = ExperimentResource(** ab_er_example)
    #     try:
    #         get_winner_assessment(er.convert_to_float())
    #     except AttributeError:
    #         pass
    
    # def test_v2_ab_w_without_wa(self):
    #     er = ExperimentResource(** ab_er_example)
    #     try:
    #         get_weights(er.convert_to_float())
    #     except AttributeError:
    #         pass

    # def test_v2_ab_without_reward(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(ab_er_example)
    #         del(eg['spec']['criteria']['rewards'])
    #         er = ExperimentResource(** eg)
    #         resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
    #         assert("No reward metric in experiment" in resp.winnerAssessment.message)
    #         assert(resp.winnerAssessment.data.winnerFound == False)
    
    # def test_v2_ab_without_reward_metric_config(self):
    #     with requests_mock.mock(real_http=True) as m:
    #         file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
    #                                  'prometheus_sample_response.json')
    #         m.get(ab_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
    #         eg = copy.deepcopy(ab_er_example)
    #         del(eg['spec']['metrics'][2])
    #         er = ExperimentResource(** eg)
    #         resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
            
    #         assert("reward metric values are not available" in resp.winnerAssessment.message)
    #         assert(resp.winnerAssessment.data.winnerFound == False)

    # def test_v2_ab_without_reward_for_feasible_version(self):
    #     eg = copy.deepcopy(ab_er_example_step2)
        
    #     del(eg['status']['analysis']['aggregatedMetrics']['data']['business-revenue']['data']['canary'])
    #     er = ExperimentResource(** eg)
    #     resp = get_winner_assessment(er.convert_to_float())
    #     assert("reward value for feasible version canary is not available" in resp.message)

    ########## A/B/N TESTS #############
    def test_v2_abn_input_object(self):
        ExperimentResource(** abn_er_example)
        ExperimentResource(** abn_er_example_step1)
        ExperimentResource(** abn_er_example_step2)
        ExperimentResource(** abn_er_example_step3)
        
    def test_experiment_abn_response_objects(self):
        AggregatedMetricsAnalysis(** abn_am_response)
        VersionAssessmentsAnalysis(** abn_va_response)
        WinnerAssessmentAnalysis(** abn_wa_response)
        WeightsAnalysis(** abn_w_response)

    def test_v2_abn_aggregated_metrics_endpoint(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            response_json = json.load(open(file_path))
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=response_json)

            expr = ExperimentResource(** abn_er_example)
            agm = get_aggregated_metrics(expr.convert_to_float()).convert_to_quantity()
            assert(agm.data['request-count'].data['default'].value == response_json['data']['result'][0]['value'][1])
        
    def test_v2_abn_version_assessment_endpoint(self):
        er = ExperimentResource(** abn_er_example_step1)
        get_version_assessments(er.convert_to_float())
    
    def test_v2_abn_winner_assessment_endpoint(self):
        er = ExperimentResource(** abn_er_example_step2)
        get_winner_assessment(er.convert_to_float())
    
    def test_v2_abn_weights_endpoint(self):
        er = ExperimentResource(** abn_er_example_step3)
        get_weights(er.convert_to_float())
    
    def test_v2_abn_analytics_assessment_endpoint(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))

            er = ExperimentResource(** abn_er_example)
            get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    def test_v2_abn_am_without_candidates(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
            eg = copy.deepcopy(abn_er_example)
            del(eg['spec']['versionInfo']['candidates'])
            er = ExperimentResource(** eg)
            get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
    
    def test_v2_abn_am_incorrect_tag_names(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
            eg = copy.deepcopy(abn_er_example)
            eg['spec']['metrics'][0]['metricObj']['spec']['params'][0]['value'] = "sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0)"
            eg['spec']['metrics'][1]['metricObj']['spec']['params'][0]['value'] = "(sum(increase(revision_app_request_latencies_sum{revision_name=~'.*$svc_name'}[$interval]))or on() vector(0)) / (sum(increase(revision_app_request_latencies_count{revision_name=~'.*$svc_name'}[$interval])) or on() vector(0))"
            eg['spec']['versionInfo']['baseline']['variables'] = [{"name": "revision_name", "value": "sample-application-v1"}]
            eg['spec']['versionInfo']['candidates'][0]['variables'] = [{"name": "revision_name", "value": "sample-application-v2"}]
            er = ExperimentResource(** eg)
            
            resp = get_aggregated_metrics(er.convert_to_float()).convert_to_quantity()
            assert("Error from metrics backend for metric" in resp.message)
    
    def test_v2_abn_analytics_assessment_conformance(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
            eg = copy.deepcopy(abn_er_example)
            del(eg['spec']['versionInfo']['candidates'])
            eg['spec']['strategy']['testingPattern'] = 'Conformance'
            er = ExperimentResource(** eg)
            get_analytics_results(er.convert_to_float()).convert_to_quantity()
    
    def test_v2_abn_version_assessment_conformance(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
 
            eg = copy.deepcopy(abn_er_example)
            del(eg['spec']['versionInfo']['candidates'])
            eg['spec']['strategy']['testingPattern'] = 'Conformance'
            er = ExperimentResource(** eg)
            resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
            assert(resp.versionAssessments.data == {'default': [True]})

    def test_v2_abn_va_without_am(self):
        er = ExperimentResource(** abn_er_example)
        try:
            get_version_assessments(er.convert_to_float())
        except AttributeError:
            pass

    def test_v2_abn_wa_without_va(self):
        er = ExperimentResource(** abn_er_example)
        try:
            get_winner_assessment(er.convert_to_float())
        except AttributeError:
            pass
    
    def test_v2_abn_w_without_wa(self):
        er = ExperimentResource(** abn_er_example)
        try:
            get_weights(er.convert_to_float())
        except AttributeError:
            pass

    def test_v2_abn_without_reward(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
            eg = copy.deepcopy(abn_er_example)
            del(eg['spec']['criteria']['rewards'])
            er = ExperimentResource(** eg)
            resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
            assert("No reward metric in experiment" in resp.winnerAssessment.message)
            assert(resp.winnerAssessment.data.winnerFound == False)
    
    def test_v2_abn_without_reward_metric_config(self):
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(abn_er_example["spec"]["metrics"][0]["metricObj"]["spec"]["urlTemplate"], json=json.load(open(file_path)))
            eg = copy.deepcopy(abn_er_example)
            del(eg['spec']['metrics'][2])
            er = ExperimentResource(** eg)
            resp = get_analytics_results(er.convert_to_float()).convert_to_quantity()
            
            assert("reward metric values are not available" in resp.winnerAssessment.message)
            assert(resp.winnerAssessment.data.winnerFound == False)

    def test_v2_abn_general(self):
        eg = copy.deepcopy(abn_er_example_step2)
        
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())
        assert(resp.data.winnerFound == True)
        assert(resp.data.winner == 'canary1')

    def test_v2_abn_without_reward_for_feasible_version(self):
        eg = copy.deepcopy(abn_er_example_step2)
        
        del(eg['status']['analysis']['aggregatedMetrics']['data']['business-revenue']['data']['canary1'])
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())
        assert("reward value for feasible version canary1 is not available" in resp.message)
        assert(resp.data.winnerFound == True)
        assert(resp.data.winner == 'canary2')
        
    def test_v2_abn_with_better_reward_but_not_feasible(self):
        eg = copy.deepcopy(abn_er_example_step2)
        
        eg['status']['analysis']['versionAssessments']['data']['canary1'] = [False]
        er = ExperimentResource(** eg)
        resp = get_winner_assessment(er.convert_to_float())
        assert(resp.data.winnerFound == True)
        assert(resp.data.winner == 'canary2')