import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.api.restplus import api
from iter8_analytics.metrics_backend.iter8metric import Iter8MetricFactory
from iter8_analytics.metrics_backend.datacapture import DataCapture
from iter8_analytics.api.analytics.successcriteria import DeltaCriterion, ThresholdCriterion
import iter8_analytics.constants as constants
import flask_restplus
from flask import request
from datetime import datetime, timezone, timedelta
import dateutil.parser as parser

import copy
import json
import os
import logging
log = logging.getLogger(__name__)


class Response():
    def __init__(self, experiment, prom_url):
        """Create response object corresponding to payload. This has everything and more."""
        self.experiment = experiment
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
        self.metric_factory = Iter8MetricFactory(prom_url)

    def compute_test_results_and_summary(self):
        self.append_metrics_and_success_criteria()
        log.info("Appended metrics and success criteria")
        self.append_assessment_summary()
        log.info("Append assessment summary")
        self.append_traffic_decision()
        log.info("Append traffic decision")


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

        if self.experiment["first_iteration"]:
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"Experiment started")
        else:
            success_criteria_met_str = "not" if not(self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]) else ""
            if self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR]:
                self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"The experiment needs to be aborted")
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"All success criteria were {success_criteria_met_str} met")

    def append_traffic_decision(self):
        last_state = self.experiment[request_parameters.LAST_STATE_STR]
        # Compute current decisions below based on increment or hold
        if self.experiment["first_iteration"] or self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]:
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

    def jsonify(self):
        return self.response
