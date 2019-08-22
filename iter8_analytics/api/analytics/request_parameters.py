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
CRITERION_ENABLE_TRAFFIC_CONTROL_STR = 'enable_traffic_control'
CRITERION_CONFIDENCE_STR = 'confidence'
CRITERION_STOP_ON_FAILURE_STR = 'stop_on_failure'


success_criterion = api.model('success_criterion', {
    METRIC_NAME_STR: fields.String(
        required=True,
        description='Name of the metric to which the criterion applies',
        example='iter8_latency'),
    METRIC_TYPE_STR: fields.String(
        required=True, enum=[PERFORMANCE_METRIC_TYPE_STR, CORRECTNESS_METRIC_TYPE_STR],
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
        description='Criterion type. Options: "delta": compares the canary '
        'against the baseline version with respect to the metric; '
        '"threshold": checks the canary with respect to the metric'),
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
    CRITERION_ENABLE_TRAFFIC_CONTROL_STR: fields.Boolean(
        required=False,
        description='Indicates whether or not this criterion is considered '
        'for traffic-control decisions; defaults to true'
    ),
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
ON_SUCCESS_VERSION_STR = 'on_success'
BASELINE_STR = 'baseline'
CANARY_STR = 'canary'
BOTH_STR = 'both'
SUCCESS_CRITERIA_STR = 'success_criteria'

traffic_control = api.model('traffic_control', {
    WARMUP_REQUEST_COUNT_STR: fields.Integer(
        required=False, example=100, min=0, default=10,
        description='Minimum number of data points required for '
        'the canary analysis; defaults to 10'),
    MAX_TRAFFIC_PERCENT_STR: fields.Float(
        required=False, example=50.0, min=0.0, default=50.0,
        description='Maximum percentage of traffic that the canary version '
        'will receive during the experiment; defaults to 50%'),
    STEP_SIZE_STR: fields.Float(
        required=False, example=2.0, min=0.1, default=1.0,
        description='Increment (in percent points) to be applied to the '
        'traffic received by the canary version each time it passes the '
        'success criteria; defaults to 1 percent point'),
    ON_SUCCESS_VERSION_STR: fields.String(
        required=False, enum=[BASELINE_STR, CANARY_STR, BOTH_STR],
        default='canary', example='canary',
        description='Determines how the traffic must be split at the end of '
        'the experiment; options: "baseline": all traffic goes to the '
        'baseline version; "canary": all traffic goes to the canary version; '
        '"both": traffic is split across baseline and canary. Defaults to '
        '"canary"'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion),
        required=True,
        description='List of criteria for assessing the canary version')
})

TRAFFIC_CONTROL_STR = 'traffic_control'

LAST_STATE_STR = '_last_state'

check_and_increment_parameters = api.model('check_and_increment_parameters', {
    BASELINE_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the baseline '
        'version'),
    CANARY_STR: fields.Nested(
        version_definition, required=True,
        description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the canary '
        'version'),
    TRAFFIC_CONTROL_STR: fields.Nested(
        traffic_control, required=True,
        description='Parameters controlling the behavior of the analytics'),
    LAST_STATE_STR: fields.Raw(
        required=True,
        description='State returned by the server on the previous call')
})
