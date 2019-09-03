import iter8_analytics.api.analytics.request_parameters as request_parameters
import iter8_analytics.api.analytics.responses as responses

from datetime import datetime, timezone, timedelta

class LastState():
    def __init__(self, baseline_traffic, candidate_traffic):
        self.last_state = {
            request_parameters.BASELINE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: baseline_traffic
            },
            request_parameters.CANDIDATE_STR: {
                responses.TRAFFIC_PERCENTAGE_STR: candidate_traffic
            }
        }

class ServicePayload():
    def __init__(self, service_payload):
        self.start_time = service_payload[request_parameters.START_TIME_PARAM_STR]
        self.end_time = str(datetime.now(timezone.utc)) if request_parameters.END_TIME_PARAM_STR not in service_payload else service_payload[request_parameters.END_TIME_PARAM_STR]
        self.tags = service_payload[request_parameters.TAGS_PARAM_STR]

class SuccessCriterion:
    def __init__(self, criterion):
        """
        criterion:  {
            "metric_name": "iter8_latency",
            "metric_type": "Performance",
            "metric_query_template": "sum(increase(istio_requests_total{response_code=~\"5..\",reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
            "metric_sample_size_query_template": "sum(increase(istio_requests_total{reporter=\"source\"}[$interval]$offset_str)) by ($entity_labels)",
            "type": "delta",
            "value": 0.02,
            "sample_size": 0,
            "stop_on_failure": false,
            "confidence": 0
            }
        """
        self.metric_name = criterion[request_parameters.METRIC_NAME_STR]
        self.metric_type = criterion[request_parameters.METRIC_TYPE_STR]
        self.metric_query_template = criterion[request_parameters.METRIC_QUERY_TEMPLATE_STR]
        self.metric_sample_size_query_template = criterion[request_parameters.METRIC_SAMPLE_SIZE_QUERY_TEMPLATE]
        self.type = criterion[request_parameters.CRITERION_TYPE_STR]
        self.value = criterion[request_parameters.CRITERION_VALUE_STR]
        self.sample_size = 10 if request_parameters.CRITERION_SAMPLE_SIZE_STR not in criterion else criterion[request_parameters.CRITERION_SAMPLE_SIZE_STR]
        self.stop_on_failure = False if request_parameters.CRITERION_STOP_ON_FAILURE_STR not in criterion else criterion[request_parameters.CRITERION_STOP_ON_FAILURE_STR]
        self.confidence = 0 if request_parameters.CRITERION_CONFIDENCE_STR not in criterion else criterion[request_parameters.CRITERION_CONFIDENCE_STR]


class TrafficControl():
    def __init__(self, traffic_control):
        self.success_criteria = []
        for each_criteria in traffic_control[request_parameters.SUCCESS_CRITERIA_STR]:
            self.success_criteria.append(SuccessCriterion(each_criteria))
        self.step_size = 2 if request_parameters.STEP_SIZE_STR not in traffic_control else traffic_control[request_parameters.STEP_SIZE_STR]
        self.max_traffic_percent = 50 if request_parameters.MAX_TRAFFIC_PERCENT_STR not in traffic_control else traffic_control[request_parameters.MAX_TRAFFIC_PERCENT_STR]
        self.warmup_request_count = 0 if request_parameters.WARMUP_REQUEST_COUNT_STR not in traffic_control else traffic_control[request_parameters.WARMUP_REQUEST_COUNT_STR]


class Experiment():
    def __init__(self, payload):
        self.experiment = {}
        if not payload[request_parameters.LAST_STATE_STR]:  # if it is empty
            last_state = LastState(100, 0)
            first_iteration = "True"
        else:
            last_state = LastState(payload[request_parameters.LAST_STATE_STR][request_parameters.BASELINE_STR][responses.TRAFFIC_PERCENTAGE_STR], payload[request_parameters.LAST_STATE_STR][request_parameters.CANDIDATE_STR][responses.TRAFFIC_PERCENTAGE_STR])
            first_iteration = "False"

        baseline_payload = ServicePayload(payload[request_parameters.BASELINE_STR])
        candidate_payload = ServicePayload(payload[request_parameters.CANDIDATE_STR])

        traffic_control = TrafficControl(payload[request_parameters.TRAFFIC_CONTROL_STR])

        self.last_state = last_state
        self.first_iteration = first_iteration
        self.baseline = baseline_payload
        self.candidate = candidate_payload
        self.traffic_control = traffic_control
