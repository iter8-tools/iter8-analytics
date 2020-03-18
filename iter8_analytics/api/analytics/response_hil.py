"""
Specification of the responses for the REST API code related analytics.
"""

from pydantic import BaseModel
from typing import List
from enum import IntEnum

####
# Schema of the response produced by
# POST /experiment/<algorithm-name>
####

#Questions/Comments:
# 1. Removed all other statistics - other than sample size and metric value
# 2. Same response outer class for all algorithms
# 3.

class StatisticalDetails(BaseModel):
    sample_size: int = Field(..., description='Number of data points collected for this '
        'success criterion')
    value: float = Field(..., description='Value computed over the sample '
        '(for "gauge" or "counter" metric types)')


class MetricDetails(BaseModel):
    metric_name: str = Field(..., description='Name identifying the metric')
    is_counter: bool = Field(..., description='Describles the type of metric. '
        'Options: "True": Metrics which are cumulative in nature and represent monotonically increasing values ; '
        '"False": Metrics which are not cumulative')
    absent_value: str = Field(None, description='Describes what value should be returned '
        'if Prometheus did not find any data corresponding to the metric')
    statistics: StatisticalDetails = Field(..., description='Measurements computed for the metric')

class TrafficSplit(BaseModel):
    baseline: float = Field(..., ge=0, le=100, description='Recommended percentage of traffic to be sent to baseline') 
    candidates: List[float] = Field(..., min_items = 1, description='Recommended percentage of traffic to be sent to each candidate')

class VersionWithMeasurements(BaseModel):
    metrics: List[MetricDetails] = Field(..., 'List of metrics and corresponding measurements')

class SuccessCriteriaResult(BaseModel):
    metric_name: str = Field(..., description='Name identifying the metric')
    conclusion: List[str]= Field(..., description='List of plain-English sentences summarizing the '
        'findings with respect to the corresponding metric')
    success_criterion_met: bool = Field(..., description='Indicates whether or not the success criterion for the '
        'corresponding metric has been met')
    abort_experiment: bool = Field(..., description='Indicates whether or not the experiment must be '
        'aborted on the basis of the criterion for this metric')

class Summary(BaseModel):
    conclusion: List[str] = Field(..., description='List of plain-English sentences summarizing the '
        'the candidate assessment')
    all_success_criteria_met: bool = Field(..., description='Indicates whether or not all success criteria for '
        'assessing the canary version have been met')
    abort_experiment: bool = Field(..., description='Indicates whether or not the experiment must be '
        'aborted based on the success criteria')

class Assessment(BaseModel):
    summary: Summary = Field(..., description='Overall summary based on all success criteria')
    success_criteria: List[SuccessCriteriaResult] = Field(..., description='Summary of results for each success criterion')

class StatusEnum(IntEnum):
    all_ok = 0 # Everything looks good from Prometheus
    prom_unreachable = 1 # Prometheus is unreachable
    invalid_prom_metric_response = 2 # Prometheus returned with metric values that are invalid -- e.g., None values for a metric with absent_value = None

class Response(BaseModel):
    baseline: VersionWithMeasurements = Field(..., description='Baseline version with measurements')
    candidate: List[VersionWithMeasurements] = Field(..., min_items = 1, description='Candidate versions with measurements')
    traffic_split_recommendation: TrafficSplit = Field(..., description = "Recommended traffic split")
    assessment: Assessment = Field(..., description='Summary of the candidate assessment')
    errors_and_warnings: StatusEnum = Field(StatusEnum.all_ok, description='Status code for this iteration -- did this iteration run without exceptions and if not, what went wrong?')
    last_state: dict = Field(..., description='State returned by the server, to be passed on the next call')
