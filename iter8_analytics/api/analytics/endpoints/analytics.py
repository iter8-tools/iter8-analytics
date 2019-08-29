"""
REST resources related to canary analytics.
"""

import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.api.restplus import api
from iter8_analytics.metrics_backend.datacapture import DataCapture
from iter8_analytics.api.analytics.iter8response import Response
from iter8_analytics.api.analytics.iter8experiment import Experiment
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
        ######################

        try:
            payload = request.get_json()
            log.info("Extracted payload")
            DataCapture.fill_value("request_payload", copy.deepcopy(payload))
            self.experiment = self.fix_experiment_defaults(payload)

            self.experiment2 = Experiment(payload)
            log.info("Fixed experiment")
            self.response_object = Response(self.experiment, prom_url)
            log.info("Created response object")
            self.response_object.compute_test_results_and_summary()
            DataCapture.fill_value("service_response", self.response_object.response)
            DataCapture.save_data()
        except Exception as e:
            flask_restplus.errors.abort(code=400, message=str(e))
        return self.response_object.jsonify()


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
            payload["first_iteration"] = True
        else:
            payload["first_iteration"] = False

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
