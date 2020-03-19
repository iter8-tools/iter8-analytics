"""
Specification of the responses for the REST API code related analytics.
"""

from pydantic import BaseModel, Field
from typing import List, Dict
from enum import IntEnum

####
# Schema of the response produced by
# POST /assessment
####

class Interval(BaseModel):
    lower: float = Field(..., le=1.0, ge = 0.0, description='Lower endpoint of the interval')
    upper: float = Field(..., le=1.0, ge = 0.0, description='Upper endpoint of the interval')

class Statistics(BaseModel):
    sample_size: int = Field(..., description='Number of data points over which this metric has been measured')
    value: float = Field(..., description='Current value of this metric')
    improvement: Interval = Field(None, description = 'Confidence interval for percentage improvement over baseline')
    probability_to_beat_baseline: float = Field(None, le = 1.0, ge = 0.0, description = 'Probability to beat baseline with respect to this metric')
    probability_to_be_best_version: float = Field(..., le = 1.0, ge = 0.0, description = 'Probability of being the best version with respect to this metric')
    confidence_interval: Interval = Field(..., description = 'Confidence interval for the value of this metric')

class SuccessCriterionAssessment(BaseModel):
    conclusion: str = Field(..., description='Human consumable description of this success criterion assessment')
    lower_threshold_breached: bool = Field(None, description = 'Indicates whether a counter metric breached the lower threshold. Relevant only for counter metrics.')
    upper_threshold_breached: bool = Field(None, description = 'Indicates whether a counter metric breached the upper threshold. Relevant only for counter metrics.')
    probability_of_meeting_success_criterion: float = Field(None, le = 1.0, ge = 0.0, description='Probability that the success criterion will be met. Relevant only for non-counter metrics.')

class Metric(BaseModel):
    id: str = Field(..., description = "ID of the metric")
    # name: str = Field(..., description='Name of the metric')
    # is_counter: bool = Field(..., description = "Is this a counter metric?")
    # lower_is_better: bool = Field(True, description =  "Are lower values of this metric better?")
    statistics: Statistics = Field(..., description='Values computed for the metric')
    success_criterion_assessment: SuccessCriterionAssessment = Field(..., description = 'Assessment of success criteria')

class VersionWithMetrics(BaseModel):
    id: str = Field(..., description = "ID of the version")
    # e.g. keys within tags: destination_service_namespace and destination_workload
    # tags: Dict[str, str] = Field(..., description='Tags for this version')
    # baseline: bool = Field(False, description = "Is this the baseline?")
    win_probability: float = Field(..., le = 1.0, ge = 0.0, description = "Probability that this version is the winner")
    request_count: int = Field(..., ge = 0, description = "Request count for this version")
    metrics: List[Metric] = Field(..., description='List of metrics and corresponding values')

class TrafficSplitRecommendation(BaseModel):
    recommendation: Dict[str, Dict[str, float]] = Field(..., description = "Traffic split recommendation on a per algorithm basis, each of which contains the percentage of traffic allocated to different versions")

class Assessment(BaseModel):
    winning_version_found: bool = Field(False, description = 'Indicates whether or not a clear winner has emerged')
    winner: str = Field(None, description = 'ID of the winning version')
    confidence_in_winner: float = Field(None, description = "Probability of the winner being the best version. This is 'None' if winner is 'None'")
    human_consumable_summary: str = Field("Experiment has just begun.", description = "Human consumable description of the assessment")

class StatusEnum(IntEnum):
    all_ok = 0 # Everything looks good from Prometheus
    prom_unreachable = 1 # Prometheus is unreachable
    invalid_prom_metric_response = 2 # Prometheus returned with metric values that are invalid -- e.g., None values for a metric with absent_value = None

class Response(BaseModel):
    versions: List[VersionWithMetrics] = Field(..., min_items = 1, description='Candidate versions with metric values')
    traffic_split_recommendation: TrafficSplitRecommendation = Field(..., description = "Traffic split recommendation on a per algorithm basis")
    # this is a dictionary which maps version ids to percentage of traffic allocated to them. The percentages need to add up to 100
    assessment: Assessment = Field(..., description='Summary of the candidate assessment')
    status: StatusEnum = Field(StatusEnum.all_ok, description='Status code for this iteration -- did this iteration run without exceptions and if not, what went wrong?')
    last_state: dict = Field(..., description='State returned by the server, to be passed on the next call')
