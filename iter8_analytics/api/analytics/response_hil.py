"""
Specification of the responses for the REST API code related analytics.
"""

from pydantic import BaseModel
from typing import List, Dict
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

class SuccessCriteriaResult(BaseModel):
    metric_name: str = Field(..., description='Name identifying the metric')
    conclusion: List[str]= Field(..., description='List of plain-English sentences summarizing the '
        'findings with respect to the corresponding metric')
    success_criterion_met: bool = Field(..., description='Indicates whether or not the success criterion for the '
        'corresponding metric has been met')
    abort_experiment: bool = Field(..., description='Indicates whether or not the experiment must be '
        'aborted on the basis of the criterion for this metric')

class MetricDetails(BaseModel):
    metric_name: str = Field(..., description='Name identifying the metric')
    is_counter: bool = Field(..., description='Describles the type of metric. '
        'Options: "True": Metrics which are cumulative in nature and represent monotonically increasing values ; '
        '"False": Metrics which are not cumulative')
    absent_value: str = Field(None, description='Describes what value should be returned '
        'if Prometheus did not find any data corresponding to the metric')
    statistics: StatisticalDetails = Field(..., description='Values computed for the metric')

class VersionWithMetrics(BaseModel):
    id: str = Field(..., description = "ID of the version")
    baseline: bool = Field(False, description = "Is this the baseline?")
    win_probability: float = Field(..., le = 1.0, ge = 0.0, description = "Probability that this version is the winner")
    request_count: int = Field(..., ge = 0, description = "Request count for this version")
    metrics: List[MetricDetails] = Field(..., 'List of metrics and corresponding values')

class Assessment(BaseModel):
    winning_version_found: bool = Field(..., description = 'Indicates whether or not a clear winner has emerged')
    human_consumable_summary: str = Field(..., description = "Human consumable description of the assessment")

class StatusEnum(IntEnum):
    all_ok = 0 # Everything looks good from Prometheus
    prom_unreachable = 1 # Prometheus is unreachable
    invalid_prom_metric_response = 2 # Prometheus returned with metric values that are invalid -- e.g., None values for a metric with absent_value = None

class Response(BaseModel):
    versions: List[VersionWithMetrics] = Field(..., min_items = 1, description='Candidate versions with metric values')
    traffic_split_recommendation: Dict[str, float] = Field(..., description = "Recommended traffic split")
    # this is a dictionary which maps version ids to percentage of traffic allocated to them. The percentages need to add up to 100
    assessment: Assessment = Field(..., description='Summary of the candidate assessment')
    status: StatusEnum = Field(StatusEnum.all_ok, description='Status code for this iteration -- did this iteration run without exceptions and if not, what went wrong?')
    last_state: dict = Field(..., description='State returned by the server, to be passed on the next call')
