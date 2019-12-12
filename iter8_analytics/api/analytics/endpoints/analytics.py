"""
REST resources related to analytics for canary releases and A/B testing
"""

import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.api.restplus import api
from iter8_analytics.metrics_backend.datacapture import DataCapture
from iter8_analytics.api.analytics.iter8response import CheckAndIncrementResponse, EpsilonTGreedyResponse, PosteriorBayesianRoutingResponse
from iter8_analytics.api.analytics.iter8experiment import CheckAndIncrementExperiment, EpsilonTGreedyExperiment, PosteriorBayesianRoutingExperiment
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
    @api.marshal_with(responses.default_response)
    def post(self):
        """Assess the candidate version and recommend traffic-control actions."""
        log.info('Started processing request to assess the candidate using the '
                 '"check_and_increment" strategy')
        log.info(f"Data Capture Mode: {DataCapture.data_capture_mode}")
        ######################

        try:
            payload = request.get_json()
            log.info("Extracted payload")
            DataCapture.fill_value("request_payload", copy.deepcopy(payload))
            self.experiment = CheckAndIncrementExperiment(payload)
            log.info("Fixed experiment")
            self.response_object = CheckAndIncrementResponse(self.experiment, prom_url)
            log.info("Created response object")
            self.response_object.compute_test_results_and_summary()

            DataCapture.fill_value("service_response", self.response_object.response)
            DataCapture.save_data()
        except Exception as e:
            flask_restplus.errors.abort(code=400, message=str(e))
        return self.response_object.jsonify()



@analytics_namespace.route('/canary/epsilon_t_greedy')
class CanaryEpsilonTGreedy(flask_restplus.Resource):

    @api.expect(request_parameters.epsilon_t_greedy_parameters,
                validate=True)
    @api.marshal_with(responses.default_response)
    def post(self):
        """Assess the candidate version and recommend traffic-control actions."""
        log.info('Started processing request to assess the candidate using the '
                 '"epsilon_t_greedy" strategy')
        log.info(f"Data Capture Mode: {DataCapture.data_capture_mode}")
        ######################

        try:
            payload = request.get_json()
            log.info("Extracted payload")
            DataCapture.fill_value("request_payload", copy.deepcopy(payload))
            self.experiment = EpsilonTGreedyExperiment(payload)
            log.info("Fixed experiment")
            self.response_object = EpsilonTGreedyResponse(self.experiment, prom_url)
            log.info("Created response object")
            self.response_object.compute_test_results_and_summary()

            DataCapture.fill_value("service_response", self.response_object.response)
            DataCapture.save_data()
        except Exception as e:
            flask_restplus.errors.abort(code=400, message=str(e))
        return self.response_object.jsonify()


@analytics_namespace.route('/canary/posterior_bayesian_routing')
class CanaryPosteriorBayesianRouting(flask_restplus.Resource):

    @api.expect(request_parameters.posterior_bayesian_routing_parameters,
                validate=True)
    @api.marshal_with(responses.default_response)
    def post(self):
        """Assess the candidate version and recommend traffic-control actions."""
        log.info('Started processing request to assess the candidate using the '
                 '"posterior_bayesian_routing" strategy')
        log.info(f"Data Capture Mode: {DataCapture.data_capture_mode}")
        ######################

        try:
            payload = request.get_json()
            log.info("Extracted payload")
            DataCapture.fill_value("request_payload", copy.deepcopy(payload))
            self.experiment = PosteriorBayesianRoutingExperiment(payload)
            # log.info("Fixed experiment")
            # self.response_object = PosteriorBayesianRoutingResponse(self.experiment, prom_url)
            # log.info("Created response object")
            # self.response_object.compute_test_results_and_summary()
        #
        #     DataCapture.fill_value("service_response", self.response_object.response)
        #     DataCapture.save_data()
        except Exception as e:
            flask_restplus.errors.abort(code=400, message=str(e))
        # return self.response_object.jsonify()
        # return self.response_object.jsonify()
        return {}
