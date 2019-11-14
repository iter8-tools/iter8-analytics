"""
Specification of the parameters for the REST API code related to analytics.
"""

from flask_restplus import fields
from iter8_analytics.api.restplus import api

####
# Schema of the request body with the parameters for
# POST /analytics/canary/check_and_increment
####
START_TIME_PARAM_STR = 'start_time'
END_TIME_PARAM_STR = 'end_time'
TAGS_PARAM_STR = 'tags'

version_definition = api.model('version_definition', {
    START_TIME_PARAM_STR: fields.DateTime(
        required=True, dt_format='iso8601', example="2019-05-01T19:00:02.389Z",
        description='ISO8601 timestamp for the beginning of the time range '
        'of interest'),
    END_TIME_PARAM_STR: fields.DateTime(
        required=False, dt_format='iso8601', example="2019-05-01T19:30:02.389Z",
        description='ISO8601 timestamp for the end of the time range of '
        'interest; if omitted, current time is assumed'),
    TAGS_PARAM_STR: fields.Raw(
        required=True,
        description='Key-value pairs identifying the data pertaining '
        'to a version',
        example={'destination_service_name': 'reviews-v2'})
})

METRIC_NAME_STR = 'metric_name'
METRIC_TYPE_STR = 'metric_type'
PERFORMANCE_METRIC_TYPE_STR = 'Performance'
CORRECTNESS_METRIC_TYPE_STR = 'Correctness'
METRIC_QUERY_TEMPLATE_STR = 'metric_query_template'
METRIC_SAMPLE_SIZE_QUERY_TEMPLATE = 'metric_sample_size_query_template'

CRITERION_TYPE_STR = 'type'
DELTA_CRITERION_STR = 'delta'
THRESHOLD_CRITERION_STR = 'threshold'
CRITERION_SAMPLE_SIZE_STR = 'sample_size'
CRITERION_VALUE_STR = 'value'
CRITERION_CONFIDENCE_STR = 'confidence'
CRITERION_STOP_ON_FAILURE_STR = 'stop_on_failure'


success_criterion_default = api.model('success_criterion_default', {
    METRIC_NAME_STR: fields.String(
        required=True,
        description='Name of the metric to which the criterion applies',
        example='iter8_error_count'),
    METRIC_TYPE_STR: fields.String(
        required=True, enum=[CORRECTNESS_METRIC_TYPE_STR, PERFORMANCE_METRIC_TYPE_STR],
        description='Metric type. Options: "Performance": Metrics which '
        'measure the performance of a microservice; '
        '"Correctness": Metrics which measure the correctness of a microservice'),
    METRIC_QUERY_TEMPLATE_STR: fields.String(
        required=True,
        description='Prometheus Query of the metric to which the criterion applies',
        example='sum(increase(istio_requests_total{response_code=~"5..",'
        'reporter="source"}[$interval]$offset_str)) by ($entity_labels)'),
    METRIC_SAMPLE_SIZE_QUERY_TEMPLATE: fields.String(
        required=True,
        description='Sample Size Query for the metric to which the criterion applies',
        example='sum(increase(istio_requests_total{reporter="source"}'
        '[$interval]$offset_str)) by ($entity_labels)'),
    CRITERION_TYPE_STR: fields.String(
        required=True, enum=[DELTA_CRITERION_STR, THRESHOLD_CRITERION_STR],
        description='Criterion type. Options: "delta": compares the candidate '
        'against the baseline version with respect to the metric; '
        '"threshold": checks the candidate with respect to the metric'),
    CRITERION_VALUE_STR: fields.Float(
        required=True, description='Value to check',
        example=0.02),
    CRITERION_SAMPLE_SIZE_STR: fields.Integer(
        required=False,
        description='Minimum number of data points required to make a '
        'decision based on this criterion; if not specified, there is '
        'no requirement on the sample size'),
    CRITERION_STOP_ON_FAILURE_STR: fields.Boolean(
        required=False, default=False,
        description='Indicates whether or not the experiment must finish if '
        'this criterion is not satisfied; defaults to false'),
    CRITERION_CONFIDENCE_STR: fields.Float(
        required=False,
        description='Indicates that this criterion is based on statistical '
        'confidence; for instance, one can specify a 98% confidence that '
        'the criterion is satisfied; if not specified, there is no confidence '
        'requirement')
})
METRIC_NATURE_STR='metric_nature'
CUMULATIVE_METRIC_TYPE_STR = 'Cumulative'
MEANABLE_METRIC_TYPE_STR = 'Meanable'
MIN_STR = "min"
MAX_STR = "max"
MIN_MAX_STR = "min, max"

min_max = api.model('min_max', {
    MIN_STR: fields.Float(
        required=True,
        description='Minimum value of the metric'),
    MAX_STR: fields.Float(
        required=True,
        description='Maximum Value of the metric')
        })
success_criterion_pbr = api.model('success_criterion_pbr', {
    METRIC_NAME_STR: fields.String(
        required=True,
        description='Name of the metric to which the criterion applies',
        example='iter8_error_count'),
    METRIC_TYPE_STR: fields.String(
        required=True, enum=[CORRECTNESS_METRIC_TYPE_STR, PERFORMANCE_METRIC_TYPE_STR],
        description='Metric type. Options: "Performance": Metrics which '
        'measure the performance of a microservice; '
        '"Correctness": Metrics which measure the correctness of a microservice'),
    METRIC_NATURE_STR: fields.String(
        required=True, enum=[CUMULATIVE_METRIC_TYPE_STR, MEANABLE_METRIC_TYPE_STR],
        description='Metric type. Options: "Cumulative": Metrics which '
        'are additive in nature'
        '"Meanable": Metrics which compute averages'),
    MIN_MAX_STR: fields.Nested(
        min_max, required=False,
        description='Minimum and Maximum value of the metric'),
    METRIC_QUERY_TEMPLATE_STR: fields.String(
        required=True,
        description='Prometheus Query of the metric to which the criterion applies',
        example='sum(increase(istio_requests_total{response_code=~"5..",'
        'reporter="source"}[$interval]$offset_str)) by ($entity_labels)'),
    METRIC_SAMPLE_SIZE_QUERY_TEMPLATE: fields.String(
        required=True,
        description='Sample Size Query for the metric to which the criterion applies',
        example='sum(increase(istio_requests_total{reporter="source"}'
        '[$interval]$offset_str)) by ($entity_labels)'),
    CRITERION_TYPE_STR: fields.String(
        required=True, enum=[DELTA_CRITERION_STR, THRESHOLD_CRITERION_STR],
        description='Criterion type. Options: "delta": compares the candidate '
        'against the baseline version with respect to the metric; '
        '"threshold": checks the candidate with respect to the metric'),
    CRITERION_VALUE_STR: fields.Float(
        required=True, description='Value to check',
        example=0.02),
    CRITERION_SAMPLE_SIZE_STR: fields.Integer(
        required=False,
        description='Minimum number of data points required to make a '
        'decision based on this criterion; if not specified, there is '
        'no requirement on the sample size'),
    CRITERION_STOP_ON_FAILURE_STR: fields.Boolean(
        required=False, default=False,
        description='Indicates whether or not the experiment must finish if '
        'this criterion is not satisfied; defaults to false'),
    CRITERION_CONFIDENCE_STR: fields.Float(
        required=False,
        description='Indicates that this criterion is based on statistical '
        'confidence; for instance, one can specify a 98% confidence that '
        'the criterion is satisfied; if not specified, there is no confidence '
        'requirement')
})

WARMUP_REQUEST_COUNT_STR = 'warmup_request_count'
MAX_TRAFFIC_PERCENT_STR = 'max_traffic_percent'
STEP_SIZE_STR = 'step_size'
BASELINE_STR = 'baseline'
CANDIDATE_STR = 'candidate'
BOTH_STR = 'both'
SUCCESS_CRITERIA_STR = 'success_criteria'

traffic_control_check_and_increment = api.model('traffic_control_check_and_increment', {
    WARMUP_REQUEST_COUNT_STR: fields.Integer(
        required=False, example=100, min=0, default=10,
        description='Minimum number of data points required for '
        'the canary analysis; defaults to 10'),
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%'),
    STEP_SIZE_STR: fields.Float(
        required=False, example=2.0, min=0.1, default=1.0,
        description='Increment (in percent points) to be applied to the '
        'traffic received by the candidate version each time it passes the '
        'success criteria; defaults to 1 percent point'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_default),
        required=True,
        description='List of criteria for assessing the candidate version')
})

traffic_control_epsilon_t_greedy = api.model('traffic_control_epsilon_t_greedy', {
    WARMUP_REQUEST_COUNT_STR: fields.Integer(
        required=False, example=100, min=0, default=10,
        description='Minimum number of data points required for '
        'the canary analysis; defaults to 10'),
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_default),
        required=True,
        description='List of criteria for assessing the candidate version')
})
POSTERIOR_SAMPLE_SIZE_STR="posterior_sample_size"
NO_OF_TRIALS_STR="no_of_trials"

traffic_control_posterior_bayesian_routing = api.model('traffic_control', {
    WARMUP_REQUEST_COUNT_STR: fields.Integer(
        required=False, example=100, min=0, default=10,
        description='Minimum number of data points required for '
        'the canary analysis; defaults to 10'),
    POSTERIOR_SAMPLE_SIZE_STR: fields.Integer(
        required=False, example=100, min=10, default=1000,
        description='Required for the traffic splitting function in the PBR algorithm'),
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%'),
    NO_OF_TRIALS_STR: fields.Float(
        required=True, example=50.0, min=1.0, default=10.0,
        description='Number of values sampled per iteration from each distribution'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_pbr),
        required=True,
        description='List of criteria for assessing the candidate version')
})

TRAFFIC_CONTROL_STR = 'traffic_control'

LAST_STATE_STR = '_last_state'

check_and_increment_parameters = api.model('check_and_increment_parameters', {
    BASELINE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the baseline '
        'version'),
    CANDIDATE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the candidate '
        'version'),
    TRAFFIC_CONTROL_STR: fields.Nested(
        traffic_control_check_and_increment, required=True,
        description='Parameters controlling the behavior of the analytics'),
    LAST_STATE_STR: fields.Raw(
        required=True,
        description='State returned by the server on the previous call')
})

epsilon_t_greedy_parameters = api.model('epsilon_t_greedy_parameters', {
    BASELINE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the baseline '
        'version'),
    CANDIDATE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the candidate '
        'version'),
    TRAFFIC_CONTROL_STR: fields.Nested(
        traffic_control_epsilon_t_greedy, required=True,
        description='Parameters controlling the behavior of the analytics'),
    LAST_STATE_STR: fields.Raw(
        required=True,
        description='State returned by the server on the previous call')
})


posterior_bayesian_routing_parameters = api.model('posterior_bayesian_routing_parameters', {
    BASELINE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the baseline '
        'version'),
    CANDIDATE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the candidate '
        'version'),
    TRAFFIC_CONTROL_STR: fields.Nested(
        traffic_control_posterior_bayesian_routing, required=True,
        description='Parameters controlling the behavior of the analytics'),
    LAST_STATE_STR: fields.Raw(
        required=True,
        description='State returned by the server on the previous call')
})
