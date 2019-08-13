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
        if not payload["_last_state"]:  # if it is empty
            last_state = {
                "baseline": {
                    "traffic_percentage": 100.0
                },
                "canary": {
                    "traffic_percentage": 0.0
                }
            }
            payload["_last_state"] = last_state
            payload["first_iteration"] = True
        else:
            payload["first_iteration"] = False

        if not "end_time" in payload["baseline"]:
            payload["baseline"]["end_time"] = str(datetime.now(timezone.utc))
        if not "end_time" in payload["canary"]:
            payload["canary"]["end_time"] = str(datetime.now(timezone.utc))

        for criterion in payload["traffic_control"]["success_criteria"]:
            if "sample_size" not in criterion:
                criterion["sample_size"] = 10

        if "step_size" not in payload["traffic_control"]:
            payload["traffic_control"]["step_size"] = 2.0
        if "max_traffic_percent" not in payload["traffic_control"]:
            payload["traffic_control"]["max_traffic_percent"] = 50

        return payload

    def create_response_object(self):
        """Create response object corresponding to payload. This has everything and more."""
        self.response = {
            "metric_backend_url": prom_url,
            "canary": {
                "metrics": [],
                "traffic_percentage": None
            },
            "baseline": {
                "metrics": [],
                "traffic_percentage": None
            },
            "assessment": {
                "summary": {},
                "success_criteria": []
            }
        }

    def append_metrics_and_success_criteria(self):
        for criterion in self.experiment["traffic_control"]["success_criteria"]:
            self.response["baseline"]["metrics"].append(self.get_results(
                criterion, self.experiment["baseline"]))
            self.response["canary"]["metrics"].append(self.get_results(
                criterion, self.experiment["canary"]))
            log.info(f"Appended metric: {criterion['metric_name']}")
            self.append_success_criteria(criterion)

    def get_results(self, criterion, entity):
        metric_spec = self.metric_factory.create_metric_spec(
            criterion, entity["tags"])
        metrics_object = self.metric_factory.get_iter8_metric(metric_spec)
        interval_str, offset_str = self.metric_factory.get_interval_and_offset_str(
            entity["start_time"], entity["end_time"])
        prometheus_results_per_success_criteria = metrics_object.get_stats(interval_str, offset_str)
        """
        prometheus_results_per_success_criteria = {'statistics': {'sample_size': '12', 'value': 13}, 'messages': ["sample_size: Query success, result found", "value: Query success, result found"]}
        """
        return {
            "metric_name": criterion["metric_name"],
            "metric_type": criterion["metric_type"],
            "statistics": prometheus_results_per_success_criteria["statistics"]
        }

    def append_success_criteria(self, criterion):
        log.info("Appending Success Criteria")
        if criterion["type"] == "delta":
            self.response["assessment"]["success_criteria"].append(DeltaCriterion(
                criterion, self.response["baseline"]["metrics"][-1], self.response["canary"]["metrics"][-1]).test())
        else:
            self.response["assessment"]["success_criteria"].append(
                ThresholdCriterion(criterion, self.response["canary"]["metrics"][-1]).test())
        log.info(" Success Criteria appended")

    def append_assessment_summary(self):
        self.response["assessment"]["summary"]["all_success_criteria_met"] = all(
            criterion["success_criterion_met"] for criterion in self.response["assessment"]["success_criteria"])
        self.response["assessment"]["summary"]["abort_experiment"] = any(
            criterion["abort_experiment"] for criterion in self.response["assessment"]["success_criteria"])
        self.response["assessment"]["summary"]["conclusions"] = []
        if ((datetime.now(timezone.utc) - parser.parse(self.experiment["baseline"]["end_time"])).total_seconds() >= 1800) or ((datetime.now(timezone.utc) - parser.parse(self.experiment["canary"]["end_time"])).total_seconds() >= 10800):
            self.response["assessment"]["summary"]["conclusions"].append("The experiment end time is more than 30 mins ago")

        if self.experiment["first_iteration"]:
            self.response["assessment"]["summary"]["conclusions"].append(f"Experiment started")
        else:
            success_criteria_met_str = "not" if not(self.response["assessment"]["summary"]["all_success_criteria_met"]) else ""
            if self.response["assessment"]["summary"]["abort_experiment"]:
                self.response["assessment"]["summary"]["conclusions"].append(f"The experiment needs to be aborted")
            self.response["assessment"]["summary"]["conclusions"].append(f"All success criteria were {success_criteria_met_str} met")

    def append_traffic_decision(self):
        last_state = self.experiment["_last_state"]
        # Compute current decisions below based on increment or hold
        if self.experiment["first_iteration"] or self.response["assessment"]["summary"]["all_success_criteria_met"]:
            new_canary_traffic_percentage = min(
                last_state["canary"]["traffic_percentage"] +
                self.experiment["traffic_control"]["step_size"],
                self.experiment["traffic_control"]["max_traffic_percent"])
        else:
            new_canary_traffic_percentage = last_state["canary"]["traffic_percentage"]
        new_baseline_traffic_percentage = 100.0 - new_canary_traffic_percentage

        self.response["_last_state"] = {
            "baseline": {
                "traffic_percentage": new_baseline_traffic_percentage
            },
            "canary": {
                "traffic_percentage": new_canary_traffic_percentage
            }
        }
        self.response["baseline"]["traffic_percentage"] = new_baseline_traffic_percentage
        self.response["canary"]["traffic_percentage"] = new_canary_traffic_percentage
