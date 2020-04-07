"""
Specification of the responses for the REST API code related analytics.
"""

# Core python stuff
from datetime import datetime
from enum import Enum
from typing import List, Dict

# Module dependencies
from pydantic import BaseModel, Field

class Interval(BaseModel):
    lower: float = Field(..., description="Lower endpoint of the interval")
    upper: float = Field(..., description="Upper endpoint of the interval")

class RatioStatistics(BaseModel):
    sample_size: int = Field(..., description="Number of data points over which the value of metric has been measured")
    improvement_over_baseline: Interval = Field(..., description = "Credible interval for percentage improvement over baseline. Defined only non-baseline versions. This is currently computed based on Bayesian estimation")
    probability_of_beating_baseline: float = Field(..., le = 1.0, ge = 0.0, description = "Probability of beating baseline with respect to this metric. Defined only for non-baseline versions. This is currently computed based on Bayesian estimation")
    probability_of_being_best_version: float = Field(..., le = 1.0, ge = 0.0, description = "Probability of being the best version with respect to this metric. This is currently computed based on Bayesian estimation")
    credible_interval: Interval = Field(..., description = "Credible interval for the value of this metric. This is currently computed based on Bayesian estimation")

class Statistics(BaseModel):
    value: float = Field(..., description="Current value of this metric")
    ratio_statistics: RatioStatistics = Field(None, description="Additional statistics. Defined only for ratio metrics")

class ThresholdAssessment(BaseModel):
    threshold_breached: bool = Field(..., description = "True if threshold is breached. False otherwise")
    probability_of_satisfying_threshold: float = Field(..., le = 1.0, ge = 0.0, description="Probability of satisfying the threshold. Defined only for ratio metrics. This is currently computed based on Bayesian estimation")

class MetricAssessment(BaseModel):
    id: str = Field(..., description = "ID of the metric")
    # name: str = Field(..., description="Name of the metric")
    # is_counter: bool = Field(..., description = "Is this a counter metric?")
    # lower_is_better: bool = Field(True, description =  "Are lower values of this metric better?")
    statistics: Statistics = Field(..., description="Statistics for this metric")
    threshold_assessment: ThresholdAssessment = Field(None, description = "Assessment of how well this metric is doing with respect to threshold. Defined only for metrics with a threshold")

class VersionAssessment(BaseModel):
    id: str = Field(..., description = "ID of the version")
    # e.g. keys within tags: destination_service_namespace and destination_workload
    # tags: Dict[str, str] = Field(..., description="Tags for this version")
    # baseline: bool = Field(False, description = "Is this the baseline?")
    request_count: int = Field(..., ge = 0, description = "Number of requests sent to this version until now")
    metric_assessments: List[MetricAssessment] = Field(..., description="Metric assessments for this version")
    win_probability: float = Field(..., description = "Probability that this version is the winner. This is currently computed based on Bayesian estimation")

class WinnerAssessment(BaseModel):
    winning_version_found: bool = Field(False, description = "Indicates whether or not a clear winner has emerged. This is currently computed based on Bayesian estimation")
    winner: str = Field(None, description = "ID of the winning version. This is currently computed based on Bayesian estimation")
    winner_posterior_probability: float = Field(None, description = "Posterior probability of the version declared as the winner being the best version. This is None if winner is None. This is currently computed based on Bayesian estimation")

class StatusEnum(str, Enum):
    no_prom_data = "no_prom_data"
    all_ok = "all_ok"
    no_last_state = "no_last_state"
    invalid_experiment_spec = "invalid_experiment_spec" # needs to be refined

class Iter8AssessmentAndRecommendation(BaseModel):
    timestamp: datetime = Field(...,
                                 description="Timestamp at which the current assessment and recommendation is created")
    baseline_assessment: VersionAssessment = Field(..., description = "Baseline's assessment")
    candidate_assessments: List[VersionAssessment] = Field(..., min_items = 1, description="Assessment  of candidate versions")
    traffic_split_recommendation: Dict[str, Dict[str, float]] = Field(..., description = "Traffic split recommendation on a per algorithm basis. Each recommendation contains the percentage of traffic on a per-version basis")
    # this is a dictionary which maps version ids to percentage of traffic allocated to them. The percentages need to add up to 100
    winner_assessment: WinnerAssessment = Field(..., description="Assessment summary for winning candidate. This is currently computed based on Bayesian estimation")
    status: List[StatusEnum] = Field([StatusEnum.all_ok], description="List of status codes for this iteration -- did this iteration run without exceptions and if not, what went wrong?")
    status_interpretations: Dict[str, str] = Field({
        StatusEnum.no_prom_data: "Incomplete Prometheus data during this iteration", 
        StatusEnum.all_ok: "Data from Prometheus available and was utilized without a glitch during this iteration", 
        StatusEnum.no_last_state: "No last state available during this iteration", 
        StatusEnum.invalid_experiment_spec: "Invalid experiment specification"
        }, 
        description="Human-friendly interpretations of the status codes returned by the analytics service") # the index of an interpretation corresponds to the corresponding status enum