import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
from iter8_analytics.api.restplus import api
from iter8_analytics.metrics_backend.iter8metric import Iter8MetricFactory
from iter8_analytics.metrics_backend.datacapture import DataCapture
from iter8_analytics.api.analytics.successcriteria import DeltaCriterion, ThresholdCriterion
from iter8_analytics.api.analytics import iter8experiment
from iter8_analytics.api.analytics.iter8experiment import BayesianRoutingLastState
import iter8_analytics.constants as constants
import flask_restplus
from flask import request
from datetime import datetime, timezone, timedelta
import dateutil.parser as parser
import numpy as np
from collections import namedtuple

import copy
import json
import os
import sys
import logging
log = logging.getLogger(__name__)


class Response():
    def __init__(self, experiment, prom_url):
        """Create response object corresponding to payload. This has everything and more."""
        self.experiment = experiment

        self.response = {
            responses.METRIC_BACKEND_URL_STR: prom_url,
            request_parameters.CANDIDATE_STR: {
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
        log.info("Appended assessment summary")
        self.append_traffic_decision()
        log.info("Appended traffic decision")

    def append_metrics_and_success_criteria(self):
        i = 0
        for criterion in self.experiment.traffic_control.success_criteria:
            self.response[request_parameters.BASELINE_STR][responses.METRICS_STR].append(self.get_results(
                criterion, self.experiment.baseline))
            self.response[request_parameters.CANDIDATE_STR][responses.METRICS_STR].append(self.get_results(
                criterion, self.experiment.candidate))
            # instead of using i we could use a unique success criterion ID
            # created by the controller to compare success criterion between two iterations
            self.append_if_metrics_changed_in_this_iteration(request_parameters.BASELINE_STR, i)
            self.append_if_metrics_changed_in_this_iteration(request_parameters.CANDIDATE_STR, i)
            i = i + 1
            log.info(f"Appended metric: {criterion.metric_name}")
            self.append_success_criteria(criterion)

    def get_results(self, criterion, entity):
        metric_spec = self.metric_factory.create_metric_spec(
            criterion, entity.tags)
        metrics_object = self.metric_factory.get_iter8_metric(metric_spec)
        interval_str, offset_str = self.metric_factory.get_interval_and_offset_str(
            entity.start_time, entity.end_time)
        prometheus_results_per_success_criteria = metrics_object.get_stats(interval_str, offset_str)
        """
        prometheus_results_per_success_criteria = {'statistics': {'sample_size': '12', 'value': 13}, 'messages': ["sample_size: Query success, result found", "value: Query success, result found"]}
        """
        return {
            request_parameters.METRIC_NAME_STR: criterion.metric_name,
            request_parameters.IS_COUNTER_STR: criterion.is_counter,
            request_parameters.ABSENT_VALUE_STR: criterion.absent_value,
            responses.STATISTICS_STR: prometheus_results_per_success_criteria[responses.STATISTICS_STR]
        }

    def append_if_metrics_changed_in_this_iteration(self, service_version, success_criterion_number):
        """
        Record any changes observed between the metrics collected in the previous iteration and the current iteration

        (i.e. between last state and current response)
            Arguments:
                `service_version`: Str; Baseline or canary
                `success_criterion_number`: int; Denotes the number of succes criterion the function is observing changes in
        """
        # Check and Increment and Epsilon t greedy require this method. PBR and OBR do not require the information captured here
        #if condition when there is no last state information- assumes that change was observed in this case
        #The next line checks if there was any last state information for 'success_criterion_number' success criteria, if not it appends current metric values to current iteration's last state
        if len(self.experiment.last_state.last_state[service_version]["success_criterion_information"]) == success_criterion_number:
            self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR] = True
            self.experiment.last_state.last_state[service_version]["success_criterion_information"].append([int(self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['sample_size']), self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['value']])

        # if condition to check if the current sample size is atleast greater than previously observed sample size
        # If yes, change was observed
        if int(self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['sample_size']) > self.experiment.last_state.last_state[service_version]["success_criterion_information"][success_criterion_number][0]:
            self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR] = True
            self.experiment.last_state.last_state[service_version]["success_criterion_information"][success_criterion_number] = [int(self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['sample_size']), self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['value']]
        #if condition to check if the current metric value is NOT the same as previously observed metric Value
        # If yes, change was observed
        elif self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['value'] != self.experiment.last_state.last_state[service_version]["success_criterion_information"][success_criterion_number][1]:
            self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR] = True
            self.experiment.last_state.last_state[service_version]["success_criterion_information"][success_criterion_number] = [int(self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['sample_size']), self.response[service_version][responses.METRICS_STR][-1][responses.STATISTICS_STR]['value']]

    def append_success_criteria(self, criterion):
        if criterion.type == request_parameters.DELTA_CRITERION_STR:
            self.response[responses.ASSESSMENT_STR][responses.SUCCESS_CRITERIA_STR].append(DeltaCriterion(
                criterion, self.response[request_parameters.BASELINE_STR][responses.METRICS_STR][-1], self.response[request_parameters.CANDIDATE_STR][responses.METRICS_STR][-1]).test())
        elif criterion.type == request_parameters.THRESHOLD_CRITERION_STR:
            self.response[responses.ASSESSMENT_STR][responses.SUCCESS_CRITERIA_STR].append(
                ThresholdCriterion(criterion, self.response[request_parameters.CANDIDATE_STR][responses.METRICS_STR][-1]).test())
        else:
            raise ValueError("Criterion type can either be Threshold or Delta")
        log.info("Appended Success Criteria")


    def append_assessment_summary(self):
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR] = all(
            criterion[responses.SUCCESS_CRITERION_MET_STR] for criterion in self.response[responses.ASSESSMENT_STR][request_parameters.SUCCESS_CRITERIA_STR])
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR] = any(
            criterion[responses.ABORT_EXPERIMENT_STR] for criterion in self.response[responses.ASSESSMENT_STR][request_parameters.SUCCESS_CRITERIA_STR])

        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR] = []
        if ((datetime.now(timezone.utc) - parser.parse(self.experiment.baseline.end_time)).total_seconds() >= 1800) or ((datetime.now(timezone.utc) - parser.parse(self.experiment.candidate.end_time)).total_seconds() >= 10800):
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append("The experiment end time is more than 30 mins ago")
        self.append_partial_assessment_summary()

    def append_partial_assessment_summary(self):
        if self.experiment.first_iteration:
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"Experiment started")
        else:
            success_criteria_met_str = "not" if not(self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]) else ""
            if self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR]:
                self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"The experiment needs to be aborted")
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"All success criteria were {success_criteria_met_str} met")
        if not self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR]:
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append("No change observed in this iteration. Traffic percentage is not altered")

        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR]["sample_size_sufficient"] = all(
            criterion["sample_size_sufficient"] for criterion in self.response[responses.ASSESSMENT_STR][request_parameters.SUCCESS_CRITERIA_STR])


    def has_baseline_met_all_criteria(self):
        """
        Function to check if baseline has met all success criteria.
        Used when candidate did not meet the success criteria
        """
        # Creating to list of bool to indidate if
        # success criteria and sample size requirements
        # are met for each criterion
        baseline_successes = []
        baseline_sample_sizes = []
        i = 0
        for criterion in self.experiment.traffic_control.success_criteria:
            # metric results obtained by Prometheus for baseline
            metric_results = self.response[request_parameters.BASELINE_STR][responses.METRICS_STR][i]

            # Assuming that in case of a delta test, the baseline passes the success criterion
            if criterion.type == request_parameters.DELTA_CRITERION_STR:
                baseline_successes.append(True)
            else:
                # in case of threshold based test we test the baseline metric collected with the user criterion
                resp = ThresholdCriterion(criterion, metric_results).test()
                # collecting a bool value (pass or fail) for each success criterion
                baseline_successes.append(resp[responses.SUCCESS_CRITERION_MET_STR])

            # checking if baseline met the sample size requirements for this criterion
            if metric_results[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] >= criterion.sample_size:
                baseline_sample_sizes.append(True)
            else:
                baseline_sample_sizes.append(False)
            i+=1
        sample_size = all(baseline_sample_sizes)
        success = all(baseline_successes)
        return sample_size, success

    def append_traffic_decision(self):
        raise NotImplementedError("Must override")

    def jsonify(self):
        return self.response

class CheckAndIncrementResponse(Response):
    def __init__(self, experiment, prom_url):
        super().__init__(experiment, prom_url)

    def append_traffic_decision(self):
        last_state = self.experiment.last_state.last_state
        # Compute current decisions below based on increment or hold
        if not self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR]:
            new_candidate_traffic_percentage = last_state[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR]
        elif self.experiment.first_iteration or self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]:
            new_candidate_traffic_percentage = min(
                last_state[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR] +
                self.experiment.traffic_control.step_size,
                self.experiment.traffic_control.max_traffic_percent)
        #else if candidate did not meet the success criteria
        else:
            #if candidate meets the sample size standards and but did not meet the success criteria
            if self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR]["sample_size_sufficient"]:
                #find out if baseline met the sample size and success criteria requirements
                sample_size, success = self.has_baseline_met_all_criteria()
                #if baseline has met sample size requirements and did not meet the success criteria
                if sample_size and not success:
                    # log this scenario and inform the user
                    self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append("The baseline version did not meet success criteria")
            new_candidate_traffic_percentage = last_state[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR]
        new_baseline_traffic_percentage = 100.0 - new_candidate_traffic_percentage

        self.response[request_parameters.LAST_STATE_STR] = {
            request_parameters.BASELINE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_baseline_traffic_percentage,
                "success_criterion_information": last_state[request_parameters.BASELINE_STR]["success_criterion_information"]
            },
            request_parameters.CANDIDATE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_candidate_traffic_percentage,
                "success_criterion_information": last_state[request_parameters.CANDIDATE_STR]["success_criterion_information"]
            }
        }
        self.response[request_parameters.BASELINE_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_baseline_traffic_percentage
        self.response[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_candidate_traffic_percentage

class EpsilonTGreedyResponse(Response):
    def __init__(self, experiment, prom_url):
        super().__init__(experiment, prom_url)

    def append_traffic_decision(self):
        last_state = self.experiment.last_state.last_state # to be cleaned up
        # If there was no change observed in this iteration then do not increment traffic percentage
        if not self.experiment.last_state.last_state[iter8experiment.CHANGE_OBSERVED_STR]:
            new_candidate_traffic_percentage = last_state[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR]
        # checking if candidate version is the best feasible option
        elif self.experiment.first_iteration or self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]:
            #Here, the candidate is the best feasible version among the two and it will be exploited
            last_state["effective_iteration_count"] = last_state["effective_iteration_count"] + 1
            epsilon = 1/last_state["effective_iteration_count"]
            exploitation_rate = int((1 - epsilon + (epsilon / 2)) * 100)
            new_candidate_traffic_percentage = min(exploitation_rate, self.experiment.traffic_control.max_traffic_percent)
        #else if candidate did not meet the success criteria
        elif not self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]:
            #if candidate did not meet the sample size standards and hence did not meet the success criteria
            if not self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR]["sample_size_sufficient"]:
                new_candidate_traffic_percentage = last_state[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR]
            #if candidate meets the sample size standards and but did not meet the success criteria
            else:
                #find out if baseline met the sample size and success criteria requirements
                sample_size, success = self.has_baseline_met_all_criteria()
                #if baseline has met sample size requirements and did not meet the success criteria
                if sample_size and not success:
                    # log this scenario and inform the user
                    self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append("The baseline version did not meet success criteria")
                #Here, the baseline is the best feasible version among the two and it will be exploited; candidate will be explored
                last_state["effective_iteration_count"] = last_state["effective_iteration_count"] + 1
                epsilon = 1/last_state["effective_iteration_count"]
                exploration_rate = int((epsilon / 2) * 100)
                new_candidate_traffic_percentage = min(exploration_rate, self.experiment.traffic_control.max_traffic_percent)
        new_baseline_traffic_percentage = 100.0 - new_candidate_traffic_percentage

        self.response[request_parameters.LAST_STATE_STR] = {
            request_parameters.BASELINE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_baseline_traffic_percentage,
                "success_criterion_information": last_state[request_parameters.BASELINE_STR]["success_criterion_information"]
            },
            request_parameters.CANDIDATE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: new_candidate_traffic_percentage,
                "success_criterion_information": last_state[request_parameters.CANDIDATE_STR]["success_criterion_information"]
            },
            "effective_iteration_count": last_state["effective_iteration_count"]
        }
        self.response[request_parameters.BASELINE_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_baseline_traffic_percentage
        self.response[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR] = new_candidate_traffic_percentage

class BayesianRoutingResponse(Response):
    def __init__(self, experiment, prom_url):
        super().__init__(experiment, prom_url)
        self.max_trials = 1000 # =this should be higher, say 10000
        self.baseline_beliefs = {}
        self.candidate_beliefs = {}
        for criterion in self.experiment.traffic_control.success_criteria:
            if not criterion.is_counter:
                self.baseline_beliefs[criterion.metric_name] = {
                request_parameters.MIN_MAX_STR: criterion.min_max,
                "params": None
                }
                self.candidate_beliefs[criterion.metric_name] = {
                request_parameters.MIN_MAX_STR: criterion.min_max,
                "params": None
                }
    def append_partial_assessment_summary(self):
        success_criteria_met_str = "not" if not(self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ALL_SUCCESS_CRITERIA_MET_STR]) else ""
        if self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.ABORT_EXPERIMENT_STR]:
            self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"The experiment needs to be aborted")
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(f"All success criteria were {success_criteria_met_str} met")

    def append_traffic_decision(self):
        """Will serve as a version of the meta algorithm """
        # Update belief for baseline and candidate version, for every metric which is not a counter.
        params = namedtuple('params', 'alpha beta gamma sigma')
        self.response[request_parameters.LAST_STATE_STR] = BayesianRoutingLastState([],[], params(None, None, None, None), params(None, None, None, None)).last_state
        i = 0
        for criterion in self.response[request_parameters.BASELINE_STR][responses.METRICS_STR]:
            if not criterion[request_parameters.IS_COUNTER_STR]:
                try:
                    self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = self.update_beliefs(criterion, self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]][request_parameters.MIN_MAX_STR])
                except Exception as e:
                    if self.experiment.first_iteration and criterion.min_max:
                        self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = params(1, 1, None, None)
                    elif self.experiment.first_iteration and not criterion.min_max:
                        self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = params(None, None, 0, 1)
                    else:
                        log.error("Prometheus query did not find usable metric value. Using previous iteration metric details")
                        last_state_beliefs = params(self.experiment.last_state.last_state[request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][0], self.experiment.last_state.last_state[request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][1], self.experiment.last_state.last_state[request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][2], self.experiment.last_state.last_state[request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][3])
                        self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = last_state_beliefs
                self.response[request_parameters.LAST_STATE_STR][request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR].append(self.baseline_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"])
            else:
                self.response[request_parameters.LAST_STATE_STR][request_parameters.BASELINE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR].append(params(None, None, None, None))
            i+=1
        i = 0
        for criterion in self.response[request_parameters.CANDIDATE_STR][responses.METRICS_STR]:
            if not criterion[request_parameters.IS_COUNTER_STR]:
                try:
                    self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = self.update_beliefs(criterion, self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]][request_parameters.MIN_MAX_STR])
                except Exception as e:
                    if self.experiment.first_iteration and criterion.min_max:
                        self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = params(1, 1, None, None)
                    elif self.experiment.first_iteration and not criterion.min_max:
                        self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = params(None, None, 0, 1)
                    else:
                        log.error("Prometheus query did not find usable metric value. Using previous iteration metric details")
                        last_state_beliefs = params(self.experiment.last_state.last_state[request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][0], self.experiment.last_state.last_state[request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][1], self.experiment.last_state.last_state[request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][2], self.experiment.last_state.last_state[request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR][i][3])
                        self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"] = last_state_beliefs
                self.response[request_parameters.LAST_STATE_STR][request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR].append(self.candidate_beliefs[criterion[request_parameters.METRIC_NAME_STR]]["params"])
            else:
                self.response[request_parameters.LAST_STATE_STR][request_parameters.CANDIDATE_STR][iter8experiment.SUCCESS_CRITERION_BELIEF_STR].append(params(None, None, None, None))
            i+=1
        routing_pmf = self.routing_pmf() # we got back the traffic split of the format {"candidate": x, "baseline": 100 - x}
        self.response[request_parameters.BASELINE_STR][responses.TRAFFIC_PERCENTAGE_STR] = routing_pmf[request_parameters.BASELINE_STR]
        self.response[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR] = routing_pmf[request_parameters.CANDIDATE_STR]

        #Append confidence string to the assessment summary
        confidence_str = "not " if self.response[request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR] < self.experiment.traffic_control.confidence*100 else ""
        confidence_str = "Required confidence of " + str(self.experiment.traffic_control.confidence) + " was "+ confidence_str + "reached"
        self.response[responses.ASSESSMENT_STR][responses.SUMMARY_STR][responses.CONCLUSIONS_STR].append(confidence_str)


    def update_beliefs(self, metric_response, min_max = None):
        """Update belief distribution for each metric
        Update beta distribution if user provided min, max values for a metric.
        Else update a normal distribution. Return the tuple (alpha, beta, gamma, sigma) -- two of these entries will be None."""
        alpha = beta = gamma = sigma = None
        params = namedtuple('params', 'alpha beta gamma sigma')
        try:
            Z = metric_response[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] * metric_response[responses.STATISTICS_STR][responses.VALUE_STR]
        except Exception as e:
            log.warning("WARNING: Prometheus query did not find usable metric value")
            raise e
        W = metric_response[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR]
        # what happens if the above value is none... ?
        if min_max:
            alpha = 1 + (Z - (min_max[request_parameters.MIN_STR]*W))/(min_max[request_parameters.MAX_STR] - min_max[request_parameters.MIN_STR])
            beta = 1 + ((min_max[request_parameters.MAX_STR]*W) - Z)/(min_max[request_parameters.MAX_STR] - min_max[request_parameters.MIN_STR])
        else:
            if metric_response[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] > 0:
                gamma = metric_response[responses.STATISTICS_STR][responses.VALUE_STR]
            else:
                gamma = 0
            sigma = np.sqrt(1/(W+1))
        return params(alpha, beta, gamma, sigma)


    def routing_pmf(self):
        """Calculates the traffic split for each version
        by counting the number of times a service version satisfies all success criteria
        out of n trials. Returns an object of the form... {"candidate": x, "baseline": 100 - x}"""
        success_count = {
            request_parameters.BASELINE_STR: 0,
            request_parameters.CANDIDATE_STR: 0
        }
        for t in range(self.max_trials):
            reward = {}
            for version in [request_parameters.BASELINE_STR, request_parameters.CANDIDATE_STR]:
                successful = True

                num_reqs = self.response[version][responses.METRICS_STR][0][responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR]
                alpha = (num_reqs + 2)/3 if version == request_parameters.BASELINE_STR else (num_reqs + 2)*2/3
                beta = (num_reqs + 2) - alpha
                # above maintains the invariant that alpha + beta = num_reqs for both versions at all times
                reward[version] = np.random.beta(a = alpha, b = beta)
                for criterion in self.experiment.traffic_control.success_criteria:
                    i = 0 # to keep track of the criterion number we are measuring
                    if not criterion.is_counter: #the metric is not cumulative
                        beliefs = self.baseline_beliefs if version == request_parameters.BASELINE_STR else self.candidate_beliefs
                        if beliefs[criterion.metric_name][request_parameters.MIN_MAX_STR]: #if min max values are defined for the metric
                            X = self.beta_sample(beliefs[criterion.metric_name]["params"].alpha, beliefs[criterion.metric_name]["params"].beta, beliefs[criterion.metric_name][request_parameters.MIN_MAX_STR][request_parameters.MIN_STR], beliefs[criterion.metric_name][request_parameters.MIN_MAX_STR][request_parameters.MAX_STR])
                        else: # if min max values are not defined for the metric
                            X = self.normal_sample(beliefs[criterion.metric_name]["params"].gamma, beliefs[criterion.metric_name]["params"].sigma)
                    else: #metric is cumulative
                        X = self.response[version][responses.METRICS_STR][i][responses.STATISTICS_STR][responses.VALUE_STR]
                    if criterion.type == request_parameters.THRESHOLD_CRITERION_STR: #feasibility constraint is Threshold
                        if X > criterion.value:
                            successful = False
                            break
                    else: #feasibility constraint is Delta
                        if not version == request_parameters.BASELINE_STR:
                            #if delta criterion is not satisfied:
                            if X > (criterion.value + 1) * self.response[request_parameters.BASELINE_STR][responses.METRICS_STR][i][responses.STATISTICS_STR][responses.VALUE_STR]:
                                successful = False
                                break
                    i+=1
                if not successful:
                    reward[version] = 0 #when the version did not meet all success criteria
            if max(reward.values()) == 0: #when neither of the versions have met the success criteria
                reward[request_parameters.BASELINE_STR] = 0.0001 #baseline gets minimum reward
            v_star = request_parameters.BASELINE_STR if reward[request_parameters.BASELINE_STR] > reward[request_parameters.CANDIDATE_STR] else request_parameters.CANDIDATE_STR # V_star = version with max reward
            success_count[v_star]+=1
        new_baseline_traffic_percentage = (success_count[request_parameters.BASELINE_STR]/self.max_trials)*100
        return {
            request_parameters.BASELINE_STR: new_baseline_traffic_percentage,
            request_parameters.CANDIDATE_STR: 100-new_baseline_traffic_percentage
        }

    def append_if_metrics_changed_in_this_iteration(self, service_version, success_criterion_number):
        """
        This function is not used in Bayesian Routing Algorithms.
        """
        pass

    def has_baseline_met_all_criteria(self):
        """
        This function is not used in Bayesian Routing Algorithms.
        It should not be called
        """
        raise NotImplementedError()

class PosteriorBayesianRoutingResponse(BayesianRoutingResponse):
    def __init__(self, experiment, prom_url):
        super().__init__(experiment, prom_url)

    @classmethod
    def beta_sample(cls, alpha, beta, min_val, max_val):
        """return a value between min and max based on beta sample"""
        x = np.random.beta(a = alpha, b = beta)
        return min_val + (max_val - min_val)*x

    @classmethod
    def normal_sample(cls, gamma, sigma):
        """return a value based on normal sample"""
        return np.random.normal(loc = gamma, scale = sigma)


class OptimisticBayesianRoutingResponse(BayesianRoutingResponse):
    def __init__(self, experiment, prom_url):
        super().__init__(experiment, prom_url)

    @classmethod
    def beta_sample(cls, alpha, beta, min_val, max_val):
        """return a value between min and max based on beta sample"""
        x = np.random.beta(a = alpha, b = beta)
        y = alpha / (alpha + beta)
        x = min(x, y)
        return min_val + (max_val - min_val)*x

    @classmethod
    def normal_sample(cls, gamma, sigma):
        """return a value based on normal sample"""
        x = np.random.normal(loc = gamma, scale = sigma)
        y = gamma
        return min(x, y)
