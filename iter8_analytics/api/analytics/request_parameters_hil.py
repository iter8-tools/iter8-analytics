"""
Specification of the request parameters for the REST API code related to analytics.
"""
# Core python stuff
from datetime import datetime
from enum import Enum
from typing import Tuple, Union, Sequence

# Module dependencies
from pydantic import BaseModel, Field

# iter8 stuff
from iter8_analytics.api.analytics.response_hil import Iter8AssessmentAndRecommendation

class Version(BaseModel):
    id: str = Field(..., description="ID of the version")
    tags: dict = Field(..., description="Key-value pairs used in prometheus queries to enable version level grouping of metrics")


class Iter8Metric(BaseModel):
    id: str = Field(..., description="ID of the metric")
    lower_is_better: bool = Field(
        ..., description="Boolean flag indicating if lower values of this metric are preferable to higher values")


# counter metric defined in iter8 configmaps
class Iter8CounterMetric(Iter8Metric):
    prom_query_template: str = Field(...,
                                     description="Prometheus query template")


class Iter8RatioMetric(Iter8Metric):  # ratio metric defined in iter8 configmaps
    numerator_prom_query_template: str = Field(
        ..., description="Prometheus query template for numerator")
    denomenator_prom_query_template: str = Field(
        ..., description="Prometheus query template for numerator")
    binary_metric: bool = Field(
        False, description="This metric is mean value of a binary variable")


class ThresholdEnum(str, Enum):
    absolute = "absolute"  # this threshold represents an absolute limit
    relative = "relative"  # this threshold represents a limit relative to baseline


class Threshold(BaseModel):
    threshold_type: ThresholdEnum = Field(..., description="Type of threshold")
    value: float = Field(..., description="Value of threshold")


class AssessmentCriterion(BaseModel):
    metric_id: str = Field(
        ..., description="ID of the metric. This matches the unique ID of the metric in iter8 metric definition")
    reward: bool = Field(
        False, description="Boolean flag indicating if this metric will be used as reward to be optimized in an A/B test. Only ratio metrics can be used as a reward. At most one metric can be used as reward")
    lower_threshold: Threshold = Field(
        None, description="Lower threshold for this metric")
    upper_threshold: Threshold = Field(
        None, description="Upper threshold for this metric")


class TrafficControlStrategy(str, Enum):
    uniform = "Uniform"
    check_and_increment = "Check and Increment"
    epsilon_t_greedy = "Decaying Epsilon Greedy"
    pbr = "Posterior Bayesian Routing"
    top_k_pbr = "Top-k Posterior Bayesian Routing"


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

# parameters for current iteration of experiment
class ExperimentIterationParameters(BaseModel):
    start_time: datetime = Field(...,
                                 description="Start time of the experiment")
    iter8_metrics: Sequence[Union[Iter8RatioMetric, Iter8CounterMetric]] = Field(
        ..., description="All iter8 metric definitions. Includes ratio and counter metrics")
    assessment_criteria: Sequence[AssessmentCriterion] = Field(
        ..., description="Specifications for metric based criteria to be assessed in this experiment")
    baseline: Version = Field(..., description="The baseline version")
    candidates: Sequence[Version] = Field(...,
                                          description="The sequence of candidates")
    advanced_traffic_control_parameters: AdvancedTrafficControlParameters = Field(
        None, description="Advanced traffic control related parameters")
    advanced_assessment_parameters: AdvancedAssessmentParameters = Field(
        None, description="Advanced assessment related parameters")
    last_state: Iter8AssessmentAndRecommendation = Field(
        None, description="Last recorded state (response) from analytics service")
