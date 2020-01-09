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
IS_COUNTER_STR = 'is_counter'
ABSENT_VALUE_STR = 'absent_value'
METRIC_QUERY_TEMPLATE_STR = 'metric_query_template'
METRIC_SAMPLE_SIZE_QUERY_TEMPLATE = 'metric_sample_size_query_template'

CRITERION_TYPE_STR = 'type'
DELTA_CRITERION_STR = 'delta'
THRESHOLD_CRITERION_STR = 'threshold'
CRITERION_SAMPLE_SIZE_STR = 'sample_size'
CRITERION_VALUE_STR = 'value'
CRITERION_STOP_ON_FAILURE_STR = 'stop_on_failure'


success_criterion_default = api.model('success_criterion_default', {
    METRIC_NAME_STR: fields.String(
        required=True,
        description='Name of the metric to which the criterion applies',
        example='iter8_error_count'),
    IS_COUNTER_STR: fields.Boolean(
        required=True, description='Describles the type of metric. '
        'Options: "True": Metrics which are cumulative in nature '
        'and represent monotonically increasing values ; '
        '"False": Metrics which are not cumulative'),
    ABSENT_VALUE_STR: fields.String(
        required=False, example="2.0", default="0.0",
        description='Describes what value should be returned '
        'if Prometheus did not find any data corresponding to the metric'),
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
        required=False, default=10,
        description='Minimum number of data points required to make a '
        'decision based on this criterion; if not specified, there is '
        'no requirement on the sample size'),
    CRITERION_STOP_ON_FAILURE_STR: fields.Boolean(
        required=False, default=False,
        description='Indicates whether or not the experiment must finish if '
        'this criterion is not satisfied; defaults to false')
})

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
success_criterion_br = api.model('success_criterion_br', {
    METRIC_NAME_STR: fields.String(
        required=True,
        description='Name of the metric to which the criterion applies',
        example='iter8_error_count'),
    IS_COUNTER_STR: fields.Boolean(
        required=True, description='Describles the type of metric. '
        'Options: "True": Metrics which are cumulative in nature '
        'and represent monotonically increasing values ; '
        '"False": Metrics which are not cumulative'),
    ABSENT_VALUE_STR: fields.String(
        required=False, example="2.0", default="0.0",
        description='Describes what value should be returned '
        'if Prometheus did not find any data corresponding to the metric'),
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
    CRITERION_STOP_ON_FAILURE_STR: fields.Boolean(
        required=False, default=False,
        description='Indicates whether or not the experiment must finish if '
        'this criterion is not satisfied; defaults to false')
})

MAX_TRAFFIC_PERCENT_STR = 'max_traffic_percent'
STEP_SIZE_STR = 'step_size'
BASELINE_STR = 'baseline'
CANDIDATE_STR = 'candidate'
BOTH_STR = 'both'
SUCCESS_CRITERIA_STR = 'success_criteria'

traffic_control_check_and_increment = api.model('traffic_control_check_and_increment', {
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
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_default),
        required=True,
        description='List of criteria for assessing the candidate version')
})


NO_OF_TRIALS_STR="no_of_trials"
CONFIDENCE_STR = "confidence"
#br = Bayesian Routing
traffic_control_br = api.model('traffic_control_br', {
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%'),
    CONFIDENCE_STR: fields.Float(
        required=False, default=0.95,
        description='Posterior probability that all '
        'success criteria is met'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_br),
        required=True,
        description='List of criteria for assessing the candidate version')})


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


bayesian_routing_parameters = api.model('bayesian_routing_parameters', {
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
         traffic_control_br, required=True,
         description='Parameters controlling the behavior of the analytics')
 })
