"""
Specification of the request parameters for the REST API code related to analytics.
"""
# Core python stuff
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Tuple, Union, Sequence

# Module dependencies
from pydantic import BaseModel, Field

# iter8 stuff
from iter8_analytics.api.analytics.response_hil import Iter8AssessmentAndRecommendation

class Version(BaseModel):
    _id: Union[int, str, UUID] = Field(..., alias = "id", description="ID of the version")
    version_labels: dict = Field(..., description="Key-value pairs used in prometheus queries to achieve version level grouping")

class DirectionEnum(str, Enum): # directions for metric values
    lower = "lower"
    higher = "higher"

class MetricSpec(BaseModel):
    _id: Union[int, str, UUID] = Field(..., alias = "id", description="ID of the metric")
    preferred_direction: DirectionEnum = Field(None, description="Indicates preference for metric values -- lower, higher, or None (default)")

# counter metric defined in iter8 configmaps
class CounterMetricSpec(MetricSpec):
    query_template: str = Field(...,
                                     description="Prometheus query template")


class RatioMetricSpec(MetricSpec):  # ratio metric = numerator counter / denominator counter
    numerator: str = Field(
        ..., description="ID of the counter metric used in numerator")
    denominator: str = Field(
        ..., description="ID of the counter metric used in denominator")
    unit_range: bool = Field(
        False, description="Boolean flag indicating if the value of this metric is always in the range 0 to 1")

class ThresholdEnum(str, Enum):
    absolute = "absolute"  # this threshold represents an absolute limit
    relative = "relative"  # this threshold represents a limit relative to baseline


class Threshold(BaseModel):
    threshold_type: ThresholdEnum = Field(..., alias = "type", description="Type of threshold")
    value: float = Field(..., description="Value of threshold")


class AssessmentCriterion(BaseModel):
    _id: Union[int, str, UUID] = Field(..., alias = "id", description = "ID of the assessment criterion")
    metric_id: Union[int, str, UUID] = Field(
        ..., description="ID of the metric. This matches the unique ID of the metric in the metric spec")
    reward: bool = Field(
        False, description="Boolean flag indicating if this metric will be used as reward to be optimized in an A/B test. Only ratio metrics can be used as a reward. At most one metric can be used as reward")
    threshold: Threshold = Field(None, description="Threshold value for this metric if any")


class Strategy(str, Enum):
    uniform = "Uniform Traffic Split"
    check_and_increment = "Simple Progressive Traffic Shift"
    epsilon_t_greedy = "Greedy Progressive Traffic Shift"
    pbr = "Bayesian Progressive Traffic Shift"
    # top_k_pbr = "Bayesian Rapid Rollout" # with a single candidate, top_k works in the same manner as uniform, so disabling this for now


class CheckAndIncrementParameters(BaseModel):
    step_size: float = Field(
        1.0, description="Minimum possible traffic increment in check and  increment")


class AdvancedTrafficControlParameters(BaseModel):
    exploration_traffic_percentage: float = Field(
        5.0, description="Percentage of traffic used for exploration", ge=0.0, le=100.0)
    check_and_increment_parameters: CheckAndIncrementParameters = Field(
        None, description="Parameters for check and increment strategy")


class AdvancedAssessmentParameters(BaseModel):
    posterior_probability_for_credible_intervals: float = Field(
        95.0, description="Posterior probability used for computing credible intervals in assessment")
    min_posterior_probability_for_winner: float = Field(
        99.0, description="Minimum value of posterior probability of being the best version which needs to be attained by a version to be declared winner")

class MetricSpecs(BaseModel):
    counter_metrics: Sequence[CounterMetricSpec] = Field(..., description = "All counter metric specs")
    ratio_metrics: Sequence[RatioMetricSpec] = Field(..., description = "All ratio metric specs")

# parameters for current iteration of experiment
class ExperimentIterationParameters(BaseModel):
    start_time: datetime = Field(...,
                                 description="Start time of the experiment")
    service_name: str = Field(..., description = "Name of the service in this experiment")
    metric_specs: MetricSpecs = Field(
        ..., description="All metric specification")
    assessment_criteria: Sequence[AssessmentCriterion] = Field(
        ..., description="Criteria to be assessed for each version in this experiment")
    baseline: Version = Field(..., description="The baseline version")
    candidates: Sequence[Version] = Field(...,
                                          description="The set of candidates")
    advanced_traffic_control_parameters: AdvancedTrafficControlParameters = Field(
        None, description="Advanced traffic control related parameters")
    advanced_assessment_parameters: AdvancedAssessmentParameters = Field(
        None, description="Advanced assessment related parameters")
    last_state: Iter8AssessmentAndRecommendation = Field(
        None, description="Last recorded state (response) from analytics service")
