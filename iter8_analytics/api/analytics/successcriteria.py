import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses
import logging
log = logging.getLogger(__name__)
SAMPLE_SIZE_SUFFICIENT_STR = 'sample_size_sufficient'
SUCCESS_STR = 'success'

class StatisticalTests: # only provides class methods for statistical tests; cannot be instantiated
    @staticmethod
    def simple_threshold(version_metric, criterion):
        #handle None response
        test_result = {
            SAMPLE_SIZE_SUFFICIENT_STR: True
        }
        if version_metric[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] < criterion.sample_size:
            test_result[SAMPLE_SIZE_SUFFICIENT_STR] = False
            test_result[SUCCESS_STR] = False
        else:
            if version_metric[responses.STATISTICS_STR][responses.VALUE_STR] == None:
                test_result[SUCCESS_STR] = False
            elif version_metric[responses.STATISTICS_STR][responses.VALUE_STR] <= criterion.value:
                test_result[SUCCESS_STR] = True
            else:
                test_result[SUCCESS_STR] = False
        return test_result

    @staticmethod
    def simple_delta(baseline_metric, candidate_metric, criterion):
        #handle None response
        if criterion.is_counter:
            raise ValueError("Delta criterion cannot be used with counter metric.")
        test_result = {
            SAMPLE_SIZE_SUFFICIENT_STR: True
        }
        if candidate_metric[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] < criterion.sample_size or baseline_metric[responses.STATISTICS_STR][responses.SAMPLE_SIZE_STR] < criterion.sample_size:
            test_result[SAMPLE_SIZE_SUFFICIENT_STR] = False
            test_result[SUCCESS_STR] = False
        else:
            if (candidate_metric[responses.STATISTICS_STR][responses.VALUE_STR] == None) or (baseline_metric[responses.STATISTICS_STR][responses.VALUE_STR] == None):
                test_result[SUCCESS_STR] = False
            elif candidate_metric[responses.STATISTICS_STR][responses.VALUE_STR] <= ((1 + criterion.value) * baseline_metric[responses.STATISTICS_STR][responses.VALUE_STR]):
                test_result[SUCCESS_STR] = True
            else:
                test_result[SUCCESS_STR] = False
        return test_result

class SuccessCriterion:
    """
    Class with methods for performing a statistical test on a metric.
    """
    def __init__(self, criterion):
        """
        criterion:  {
                        "metric_name": "iter8_error_count",
                        "is_counter": True,
                        "absent_value": "0",
                        "metric_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',response_code=~'5..',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "metric_sample_size_query_template": "sum(increase(istio_requests_total{source_workload_namespace!='knative-serving',reporter='source'}[$interval]$offset_str)) by ($entity_labels)",
                        "type": "delta",
                        "value": 0.02,
                        "sample_size": 0,
                        "stop_on_failure": false,
                        "confidence": 0
                    }
        """
        self.criterion = criterion

    def test(self):
        raise NotImplementedError()

    def post_process_test_result(self, test_result):
        is_or_is_not = "is" if test_result[SUCCESS_STR] else "is not"
        delta_or_threshold = "delta" if self.criterion.type == "delta" else "threshold"
        baseline_str = "of the baseline" if self.criterion.type == "delta" else ""
        result_str = f"{self.criterion.metric_name} of the candidate {is_or_is_not} within {delta_or_threshold} {self.criterion.value} {baseline_str}. "
        conclusion_str = ["Insufficient sample size. " if not test_result[SAMPLE_SIZE_SUFFICIENT_STR] else result_str]
        counter_exceeded = True if (self.criterion.is_counter and test_result[SAMPLE_SIZE_SUFFICIENT_STR] and not test_result[SUCCESS_STR]) else False
        if counter_exceeded:
            conclusion_str.append("Counter Metric exceeded threshold value. Aborting experiment.")

        return {
            request_parameters.METRIC_NAME_STR: self.criterion.metric_name,
            responses.CONCLUSIONS_STR: conclusion_str,
            responses.SUCCESS_CRITERION_MET_STR: test_result[SUCCESS_STR],
            responses.ABORT_EXPERIMENT_STR: (self.criterion.stop_on_failure and test_result[SAMPLE_SIZE_SUFFICIENT_STR] and not test_result[SUCCESS_STR]) or (counter_exceeded),
            SAMPLE_SIZE_SUFFICIENT_STR: test_result[SAMPLE_SIZE_SUFFICIENT_STR]
        }

    def post_process_test_result_bayesian(self, test_result):
        is_or_is_not = "is" if test_result[SUCCESS_STR] else "is not"
        delta_or_threshold = "delta" if self.criterion.type == "delta" else "threshold"
        baseline_str = "of the baseline" if self.criterion.type == "delta" else ""
        result_str = f"{self.criterion.metric_name} of the candidate {is_or_is_not} within {delta_or_threshold} {self.criterion.value} {baseline_str}. "
        conclusion_str = [result_str]
        counter_exceeded = True if (self.criterion.is_counter and test_result[SAMPLE_SIZE_SUFFICIENT_STR] and not test_result[SUCCESS_STR]) else False
        if counter_exceeded:
            conclusion_str.append("Counter Metric exceeded threshold value. Aborting experiment.")

        return {
            request_parameters.METRIC_NAME_STR: self.criterion.metric_name,
            responses.CONCLUSIONS_STR: conclusion_str,
            responses.SUCCESS_CRITERION_MET_STR: test_result[SUCCESS_STR],
            responses.ABORT_EXPERIMENT_STR: (self.criterion.stop_on_failure and test_result[SAMPLE_SIZE_SUFFICIENT_STR] and not test_result[SUCCESS_STR]) or (counter_exceeded),
        }

class DeltaCriterion(SuccessCriterion):
    def __init__(self, criterion, baseline_metrics, candidate_metrics):
        super().__init__(criterion)
        self.baseline_metric = baseline_metrics
        self.candidate_metric = candidate_metrics

    def test(self):
        # t_delta, bernoulli_delta are the other options beyond simple_delta
        test_result = StatisticalTests.simple_delta(self.baseline_metric, self.candidate_metric, self.criterion)
        return self.post_process_test_result(test_result)

    def test_bayesian(self):
        # t_delta, bernoulli_delta are the other options beyond simple_delta
        test_result = StatisticalTests.simple_delta(self.baseline_metric, self.candidate_metric, self.criterion)
        return self.post_process_test_result_bayesian(test_result)


class ThresholdCriterion(SuccessCriterion):
    def __init__(self, criterion, version_metrics):
        super().__init__(criterion)
        self.version_metric = version_metrics

    def test(self):
        # t_test, bernoulli_test are the other options beyond simple_threshold
        test_result = StatisticalTests.simple_threshold(self.version_metric, self.criterion)
        return self.post_process_test_result(test_result)
