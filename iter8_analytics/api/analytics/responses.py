"""
Specification of the responses for the REST API code related analytics.
"""

from flask_restplus import fields
from iter8_analytics.api.restplus import api
import iter8_analytics.api.analytics.request_parameters as request_parameters

####
# Schema of the response produced by
# POST /analytics/canary/check_and_increment
####

SAMPLE_SIZE_STR = 'sample_size'
MIN_STR = 'min'
MAX_STR = 'max'
MEAN_STR = 'mean'
STDDEV_STR = 'stddev'
FIRST_QUARTILE_STR = 'first_quartile'
MEDIAN_STR = 'median'
THIRD_QUARTILE_STR = 'third_quartile'
PERCENTILE_95TH_STR = '95th_percentile'
PERCENTILE_99TH_STR = '99th_percentile'
VALUE_STR = 'value'

stat_details = api.model('stat_details', {
    SAMPLE_SIZE_STR: fields.Integer(
        required=True, min=0, example=200,
        description='Number of data points collected'),
    MIN_STR: fields.Float(
        required=True, min=0.0, example=2.3,
        description='Minimum value in the sample '
        '(for "histogram" metric types)'),
    MAX_STR: fields.Float(
        required=True, min=0.0, example=987.7,
        description='Maximum value in the sample'
        '(for "histogram" metric types)'),
    MEAN_STR: fields.Float(
        required=True, min=0.0, example=327.4,
        description='Mean of the sample'
        '(for "histogram" metric types)'),
    STDDEV_STR: fields.Float(
        required=True, min=0.0, example=57.3,
        description='Standard deviation of the sample'
        '(for "histogram" metric types)'),
    FIRST_QUARTILE_STR: fields.Float(
        required=True, min=0.0, example=21.4,
        description='First quartile of the sample'
        '(for "histogram" metric types)'),
    MEDIAN_STR: fields.Float(
        required=True, min=0.0, example=321.9,
        description='Median of the sample'
        '(for "histogram" metric types)'),
    THIRD_QUARTILE_STR: fields.Float(
        required=True, min=0.0, example=602.8,
        description='Third quartile of the sample'
        '(for "histogram" metric types)'),
    PERCENTILE_95TH_STR: fields.Float(
        required=True, min=0.0, example=910.2,
        description='95th percentile of the sample'
        '(for "histogram" metric types)'),
    PERCENTILE_99TH_STR: fields.Float(
        required=True, min=0.0, example=986.9,
        description='99th percentile the sample'
        '(for "histogram" metric types)'),
    VALUE_STR: fields.Float(
        required=True, min=0.0,
        description='Value computed over the sample '
        '(for "gauge" or "counter" metric types)')
})

METRIC_BACKEND_URL_STR = 'metric_backend_url'
METRIC_NAME_STR = 'metric_name'
METRIC_TYPE_STR = 'metric_type'
STATISTICS_STR = 'statistics'

metric_details = api.model('metric_details', {
    METRIC_NAME_STR: fields.String(
        required=True, example='iter8_latency',
        description='Name identifying the metric'),
    METRIC_TYPE_STR: fields.String(
        required=True,
        enum=[request_parameters.CORRECTNESS_METRIC_TYPE_STR, request_parameters.PERFORMANCE_METRIC_TYPE_STR],
        example=request_parameters.CORRECTNESS_METRIC_TYPE_STR, description='Metric type'),
    STATISTICS_STR: fields.Nested(
        stat_details, required=True,
        description='Measurements computed for the metric')
})

METRICS_STR = 'metrics'
TRAFFIC_PERCENTAGE_STR = 'traffic_percentage'

version_measurements = api.model('version_measurements', {
    METRICS_STR: fields.List(
        fields.Nested(metric_details),
        required=True,
        description='List of metrics and corresponding measurements'),
    TRAFFIC_PERCENTAGE_STR: fields.Float(
        required=True,
        min=0.0, example=10.0,
        description='Recommended percentage of traffic to be sent to this '
        'version')
})

CONCLUSIONS_STR = 'conclusions'
ALL_SUCCESS_CRITERIA_MET_STR = 'all_success_criteria_met'
SUCCESS_CRITERION_MET_STR = 'success_criterion_met'
ABORT_EXPERIMENT_STR = 'abort_experiment'

summary = api.model('summary', {
    CONCLUSIONS_STR: fields.List(
        fields.String, required=True,
        example=[
            'Data does not support the conclusion that the candidate '
            'succeeded.',
            'Experiment can continue safely.'
        ],
        description='List of plain-English sentences summarizing the '
        'the candidate assessment'),
    ALL_SUCCESS_CRITERIA_MET_STR: fields.Boolean(
        required=True, example=False, default=False,
        description='Indicates whether or not all success criteria for '
        'assessing the canary version have been met'
    ),
    ABORT_EXPERIMENT_STR: fields.Boolean(
        required=True, example=False, default=False,
        description='Indicates whether or not the experiment must be '
        'aborted based on the success criteria'
    )
})

success_criterion_output = api.model('success_criterion_output', {
    METRIC_NAME_STR: fields.String(
        required=True, example='iter8_latency',
        description='Name identifying the metric'),
    CONCLUSIONS_STR: fields.List(
        fields.String, required=True,
        example=['iter8_latency of the candidate is within 0.1 of the '
                 'baseline'],
        description='List of plain-English sentences summarizing the '
        'findings with respect to the corresponding metric'),
    SUCCESS_CRITERION_MET_STR: fields.Boolean(
        required=True, example=False, default=False,
        description='Indicates whether or not the success criterion for the '
        'corresponding metric has been met'
    ),
    ABORT_EXPERIMENT_STR: fields.Boolean(
        required=True, example=False, default=False,
        description='Indicates whether or not the experiment must be '
        'aborted on the basis of the criterion for this metric'
    )
})

SUMMARY_STR = 'summary'
SUCCESS_CRITERIA_STR = 'success_criteria'

assessment = api.model('assessment', {
    SUMMARY_STR: fields.Nested(
        summary,
        required=True,
        description='Overall summary based on all success criteria'),
    SUCCESS_CRITERIA_STR: fields.List(
        fields.Nested(success_criterion_output),
        required=True,
        description='Summary of results for each success criterion')
})

ASSESSMENT_STR = 'assessment'
ALPHA_BETA_STR = 'alpha_beta'
default_response = api.model('default_response', {
    METRIC_BACKEND_URL_STR: fields.String(
        required=True,
        example='http://localhost:9090',
        description='URL to query the time-series database'),
    request_parameters.BASELINE_STR: fields.Nested(
        version_measurements,
        required=True,
        description='Measurements and traffic recommendation for the '
        'baseline version'),
    request_parameters.CANDIDATE_STR: fields.Nested(
        version_measurements,
        required=True,
        description='Measurements and traffic recommendation for the '
        'candidate version'),
    ASSESSMENT_STR: fields.Nested(
        assessment,
        required=True,
        description='Summary of the candidate assessment based on success '
        'criteria'),
    request_parameters.LAST_STATE_STR: fields.Raw(
        required=True,
        description='State returned by the server, to be passed on the '
        'next call')
})
