"""
REST resources related to canary analytics.
"""

import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.api.restplus import api
from iter8_analytics.metrics_backend.iter8metric import Iter8MetricFactory
from iter8_analytics.metrics_backend.datacapture import DataCapture
from iter8_analytics.metrics_backend.successcriteria import DeltaCriterion, ThresholdCriterion
import iter8_analytics.constants as constants
import flask_restplus
from flask import request
from datetime import datetime, timezone, timedelta
import dateutil.parser as parser


import json
import os
import logging
import copy

log = logging.getLogger(__name__)

prom_url = os.getenv(constants.ITER8_ANALYTICS_METRICS_BACKEND_URL_ENV)
DataCapture.data_capture_mode = os.getenv(constants.ITER8_DATA_CAPTURE_MODE_ENV)


analytics_namespace = api.namespace(
    'analytics',
    description='Operations to support canary releases and A/B tests')

#################
# REST API
#################


@analytics_namespace.route('/canary/check_and_increment')
class CanaryCheckAndIncrement(flask_restplus.Resource):

    @api.expect(request_parameters.check_and_increment_parameters,
                validate=True)
    @api.marshal_with(responses.check_and_increment_response)
    def post(self):
        """Assess the canary version and recommend traffic-control actions."""
        log.info('Started processing request to assess the canary using the '
                 '"check_and_increment" strategy')
        log.info(f"Data Capture Mode: {DataCapture.data_capture_mode}")
        try:
            self.metric_factory = Iter8MetricFactory(prom_url)
            payload = request.get_json()
            log.info("Extracted payload")
            DataCapture.fill_value("request_payload", copy.deepcopy(payload))
            self.experiment = self.fix_experiment_defaults(payload)
            log.info("Fixed experiment")
            self.create_response_object()
            log.info("Created response object")
            self.append_metrics_and_success_criteria()
            log.info("Appended metrics and success criteria")
            self.append_assessment_summary()
            log.info("Append assessment summary")
            self.append_traffic_decision()
            log.info("Append traffic decision")
            DataCapture.fill_value("service_response", self.response)
            DataCapture.save_data()
        except Exception as e:
            flask_restplus.errors.abort(code=400, message=str(e))
        return self.response

    def fix_experiment_defaults(self, payload):
        if not payload[request_parameters.LAST_STATE_STR]:  # if it is empty
            last_state = {
                request_parameters.BASELINE_STR: {
                    responses.TRAFFIC_PERCENTAGE_STR: 100.0
                },
                request_parameters.CANARY_STR: {
                    responses.TRAFFIC_PERCENTAGE_STR: 0.0
                }
            }
            payload[request_parameters.LAST_STATE_STR] = last_state
            payload[request_parameters.FIRST_ITERATION_STR] = True
        else:
            payload[request_parameters.FIRST_ITERATION_STR] = False

        if not request_parameters.END_TIME_PARAM_STR in payload[request_parameters.BASELINE_STR]:
            payload[request_parameters.BASELINE_STR][request_parameters.END_TIME_PARAM_STR] = str(datetime.now(timezone.utc))
        if not request_parameters.END_TIME_PARAM_STR in payload[request_parameters.CANARY_STR]:
            payload[request_parameters.CANARY_STR][request_parameters.END_TIME_PARAM_STR] = str(datetime.now(timezone.utc))

        for criterion in payload[request_parameters.TRAFFIC_CONTROL_STR][request_parameters.SUCCESS_CRITERIA_STR]:
            if request_parameters.CRITERION_SAMPLE_SIZE_STR not in criterion:
                criterion[request_parameters.CRITERION_SAMPLE_SIZE_STR] = 10

        if request_parameters.STEP_SIZE_STR not in payload[request_parameters.TRAFFIC_CONTROL_STR]:
            payload[request_parameters.TRAFFIC_CONTROL_STR][request_parameters.STEP_SIZE_STR] = 2.0
        if request_parameters.MAX_TRAFFIC_PERCENT_STR not in payload[request_parameters.TRAFFIC_CONTROL_STR]:
            payload[request_parameters.TRAFFIC_CONTROL_STR][request_parameters.MAX_TRAFFIC_PERCENT_STR] = 50

        return payload

    def create_response_object(self):
        """Create response object corresponding to payload. This has everything and more."""
        self.response = {
            responses.METRIC_BACKEND_URL_STR: prom_url,
            request_parameters.CANARY_STR: {
                responses.METRICS_STR: [],
                responses.TRAFFIC_PERCENTAGE_STR: None
            },
            request_parameters.BASELINE_STR: {
                responses.METRICS_STR: [],
                responses.TRAFFIC_PERCENTAGE_STR: None
            },
            responses.ASSESSMENT_STR: {
                responses.SUMMARY_STR: {},
                responses.SUCCESS_CRITERIA_STR: []
            }
        }

    def append_metrics_and_success_criteria(self):
        for criterion in self.experiment[request_parameters.TRAFFIC_CONTROL_STR][responses.SUCCESS_CRITERIA_STR]:
            self.response[request_parameters.BASELINE_STR][responses.METRICS_STR].append(self.get_results(
                criterion, self.experiment[request_parameters.BASELINE_STR]))
            self.response[request_parameters.CANARY_STR][responses.METRICS_STR].append(self.get_results(
                criterion, self.experiment[request_parameters.CANARY_STR]))
            log.info(f"Appended metric: {criterion[request_parameters.METRIC_NAME_STR]}")
            self.append_success_criteria(criterion)

    def get_results(self, criterion, entity):
        metric_spec = self.metric_factory.create_metric_spec(
            criterion, entity[request_parameters.TAGS_PARAM_STR])
        metrics_object = self.metric_factory.get_iter8_metric(metric_spec)
        interval_str, offset_str = self.metric_factory.get_interval_and_offset_str(
            entity[request_parameters.START_TIME_PARAM_STR], entity[request_parameters.END_TIME_PARAM_STR])
        prometheus_results_per_success_criteria = metrics_object.get_stats(interval_str, offset_str)
        """
        prometheus_results_per_success_criteria = {'statistics': {'sample_size': '12', 'value': 13}, 'messages': ["sample_size: Query success, result found", "value: Query success, result found"]}
        """
        return {
            request_parameters.METRIC_NAME_STR: criterion[request_parameters.METRIC_NAME_STR],
            request_parameters.METRIC_TYPE_STR: criterion[request_parameters.METRIC_TYPE_STR],
            responses.STATISTICS_STR: prometheus_results_per_success_criteria[responses.STATISTICS_STR]
        }

    def append_success_criteria(self, criterion):
        log.info("Appending Success Criteria")
        if criterion[request_parameters.CRITERION_TYPE_STR] == request_parameters.DELTA_CRITERION_STR:
            self.response[responses.ASSESSMENT_STR][responses.SUCCESS_CRITERIA_STR].append(DeltaCriterion(
                criterion, self.response[request_parameters.BASELINE_STR][responses.METRICS_STR][-1], self.response[request_parameters.CANARY_STR][responses.METRICS_STR][-1]).test())
        elif criterion[request_parameters.CRITERION_TYPE_STR] == request_parameters.THRESHOLD_CRITERION_STR:
            self.response[responses.ASSESSMENT_STR][responses.SUCCESS_CRITERIA_STR].append(
                ThresholdCriterion(criterion, self.response[request_parameters.CANARY_STR][responses.METRICS_STR][-1]).test())
        else:
            raise ValueError("Criterion type can either be Threshold or Delta")
        log.info(" Success Criteria appended")

    def append_assessment_summary(self):
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR] = all(
            criterion[responses.SUCCESS_CRITERION_MET_STR] for criterion in self.response[responses.ASSESSMENT_STR][request_parameters.SUCCESS_CRITERIA_STR])
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR] = any(
            criterion[responses.ABORT_EXPERIMENT_STR] for criterion in self.response[responses.ASSESSMENT_STR][request_parameters.SUCCESS_CRITERIA_STR])
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR] = []
        if ((datetime.now(timezone.utc) - parser.parse(self.experiment[request_parameters.BASELINE_STR][request_parameters.END_TIME_PARAM_STR])).total_seconds() >= 1800) or ((datetime.now(timezone.utc) - parser.parse(self.experiment["canary"]["end_time"])).total_seconds() >= 10800):
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append("The experiment end time is more than 30 mins ago")

        if self.experiment[request_parameters.FIRST_ITERATION_STR]:
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"Experiment started")
        else:
            success_criteria_met_str = "not" if not(self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]) else ""
            if self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR]:
                self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"The experiment needs to be aborted")
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"All success criteria were {success_criteria_met_str} met")

    def append_traffic_decision(self):
        last_state = self.experiment[request_parameters.LAST_STATE_STR]
        # Compute current decisions below based on increment or hold
        if self.experiment[request_parameters.FIRST_ITERATION_STR] or self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]:
            new_canary_traffic_percentage = min(
                last_state[request_parameters.CANARY_STR][responses.TRAFFIC_PERCENTAGE_STR] +
                self.experiment[request_parameters.TRAFFIC_CONTROL_STR][request_parameters.STEP_SIZE_STR],
                self.experiment[request_parameters.TRAFFIC_CONTROL_STR][request_parameters.MAX_TRAFFIC_PERCENT_STR])
        else:
            new_canary_traffic_percentage = last_state[request_parameters.CANARY_STR][responses.TRAFFIC_PERCENTAGE_STR]
        new_baseline_traffic_percentage = 100.0 - new_canary_traffic_percentage

        self.response[request_parameters.LAST_STATE_STR] = {
            request_parameters.BASELINE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_baseline_traffic_percentage
            },
            request_parameters.CANARY_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_canary_traffic_percentage
            }
        }
        self.response[request_parameters.BASELINE_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_baseline_traffic_percentage
        self.response[request_parameters.CANARY_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_canary_traffic_percentage
