"""Tests for the SuccessCriteria class."""

import unittest
from unittest.mock import Mock
from unittest.mock import patch
from requests.models import Response

import json
from iter8_analytics import app as flask_app
from iter8_analytics.api.analytics import responses as responses
from iter8_analytics.api.analytics import request_parameters as request_parameters
import iter8_analytics.constants as constants
from iter8_analytics.api.analytics.successcriteria import StatisticalTests, SuccessCriterion, DeltaCriterion, ThresholdCriterion
import dateutil.parser as parser
from iter8_analytics.api.analytics.iter8experiment import FeasibilityCriterionDefault as FCD

import logging
import os
import requests_mock
import requests
log = logging.getLogger(__name__)

import re

from urllib.parse import urlencode

class TestAnalyticsAPI(unittest.TestCase):
    def test_abort_experiment(self):
        criterion = FCD({
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": True,
                        "metric_query_template": "iter8-error-rate-query-template",
                        "metric_sample_size_query_template": "sample-size-query-template",
                        "sample_size": 0
                    })
        sc = SuccessCriterion(criterion)

        tr = sc.update_response_with_test_result_and_conclusion({
            "sample_size_sufficient": False,
            "success": False
        })
        assert(not tr["abort_experiment"])

        #Test for counter metric and success = False
        criterion = FCD({
                        "metric_name": "iter8_error_rate",
                        "is_counter": False,
                        "absent_value": "0.0",
                        "type": "threshold",
                        "value": 0.02,
                        "stop_on_failure": True,
                        "metric_query_template": "iter8-error-rate-query-template",
                        "metric_sample_size_query_template": "sample-size-query-template",
                        "sample_size": 0
                    })
        sc = SuccessCriterion(criterion)

        tr = sc.update_response_with_test_result_and_conclusion({
            "sample_size_sufficient": True,
            "success": False
        })
        assert(tr["abort_experiment"])

    def test_each_criterion(self):
        #Testing Threshold Criterion
        criterion = FCD({
        "metric_name": "iter8_error_count",
        "is_counter": True,
        "absent_value": "0.0",
        "metric_query_template": "query_template",
        "metric_sample_size_query_template": "query_template",
        "type": "threshold",
        "value": 10,
        "sample_size": 10
        })

        candidate_metrics = {
        "metric_name": "iter8_error_count",
        "is_counter": True,
        "absent_value": "0",
        "statistics": {'sample_size': 12, 'value': 13}
        }

        tc = ThresholdCriterion(criterion, candidate_metrics).test()

        assert "iter8_error_count of the candidate is not within threshold 10 . " in tc["conclusions"]
        self.assertEqual(tc["success_criterion_met"], False)


        candidate_metrics["statistics"]["value"] = 9

        tc = ThresholdCriterion(criterion, candidate_metrics).test()

        assert "iter8_error_count of the candidate is within threshold 10 . " in tc["conclusions"][0]
        self.assertEqual(tc["success_criterion_met"], True)

        #Testing Delta criterion

        baseline_metrics = {
        "metric_name": "iter8_error_rate",
        "is_counter": False,
        "absent_value": "0.0",
        "statistics": {'sample_size': 30, 'value': 12}
        }
        criterion.metric_name = "iter8_error_rate"
        criterion.is_counter = False
        criterion.type = "delta"
        criterion.value = 0.5

        baseline_metrics["statistics"]["value"] = 10
        candidate_metrics["statistics"]["value"] = 12


        dc = DeltaCriterion(criterion, baseline_metrics, candidate_metrics).test()
        assert "iter8_error_rate of the candidate is within delta 0.5 of the baseline." in dc["conclusions"][0]
        self.assertEqual(dc["success_criterion_met"], True)


        candidate_metrics["statistics"]["value"] = 20

        dc = DeltaCriterion(criterion, baseline_metrics, candidate_metrics).test()
        assert "iter8_error_rate of the candidate is not within delta 0.5 of the baseline." in dc["conclusions"][0]
        self.assertEqual(dc["success_criterion_met"], False)


    def test_sample_size(self):
        #Testing Threshold Criterion
        criterion = FCD({
        "metric_name": "iter8_error_rate",
        "is_counter": False,
        "absent_value": "0.0",
        "metric_query_template": "query_template",
        "metric_sample_size_query_template": "query_template",
        "type": "threshold",
        "value": 10,
        "sample_size": 20
        })

        candidate_metrics = {
        "metric_name": "iter8_error_rate",
        "is_counter": False,
        "absent_value": "0.0",
        "statistics": {'sample_size': 10, 'value': 12}
        }

        tc = ThresholdCriterion(criterion, candidate_metrics).test()
        assert "Insufficient sample size." in tc["conclusions"][0]
        self.assertEqual(tc["success_criterion_met"], False)

        baseline_metrics = {
        "metric_name": "iter8_error_rate",
        "is_counter": False,
        "absent_value": "0.0",
        "statistics": {'sample_size': 12, 'value': 13}
        }

        dc = DeltaCriterion(criterion, baseline_metrics, candidate_metrics).test()
        assert "Insufficient sample size." in dc["conclusions"][0]
        self.assertEqual(dc["success_criterion_met"], False)

    def test_threshold_exceeded_for_counter(self):
        #Testing Threshold Criterion
        criterion = FCD({
        "metric_name": "iter8_error_count",
        "is_counter": True,
        "absent_value": "0.0",
        "metric_query_template": "query_template",
        "metric_sample_size_query_template": "query_template",
        "type": "threshold",
        "value": 10,
        "sample_size": 10
        })

        candidate_metrics = {
        "metric_name": "iter8_error_count",
        "is_counter": True,
        "absent_value": "0.0",
        "statistics": {'sample_size': 12, 'value': 13}
        }

        tc = ThresholdCriterion(criterion, candidate_metrics).test()

        assert "iter8_error_count of the candidate is not within threshold 10 . " in tc["conclusions"]
        assert "Counter Metric exceeded threshold value. Aborting experiment." in tc["conclusions"]
        self.assertEqual(tc["success_criterion_met"], False)
