"""
Pydantic data model for iter8 experiment iteration request
"""
# Core python stuff
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Tuple, Union, Sequence, Dict, Any

# Module dependencies
from pydantic import BaseModel, Field

# iter8 stuff
from iter8_analytics.api.analytics.experiment_iteration_response import Iter8AssessmentAndRecommendation

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

class MetricSpecs(BaseModel):
    counter_metrics: Sequence[CounterMetricSpec] = Field(..., description = "All counter metric specs")
    ratio_metrics: Sequence[RatioMetricSpec] = Field(..., description = "All ratio metric specs")

class ThresholdEnum(str, Enum):
    absolute = "absolute"  # this threshold represents an absolute limit
    relative = "relative"  # this threshold represents a limit relative to baseline

class Threshold(BaseModel):
    threshold_type: ThresholdEnum = Field(..., alias = "type", description="Type of threshold")
    value: float = Field(..., description="Value of threshold")

class Criterion(BaseModel):
    _id: Union[int, str, UUID] = Field(..., alias = "id", description = "ID of the criterion")
    metric_id: Union[int, str, UUID] = Field(
        ..., description="ID of the metric. This matches the unique ID of the metric in the metric spec")
    reward: bool = Field(
        False, description="Boolean flag indicating if this metric will be used as reward to be optimized in an A/B test. Only ratio metrics can be used as a reward. At most one metric can be used as reward")
    threshold: Threshold = Field(None, description="Threshold value for this metric if any")

class TrafficSplitStrategy(str, Enum):
    pbr = "Progressive Rollout"
    top_2_pbr = "Rapid Winner Identification"

class TrafficControlParameters(BaseModel):
    strategy: TrafficSplitStrategy = Field(None, description = "Traffic split strategy")
    exploration_traffic_percentage: float = Field(
        5.0, description="Percentage of traffic used for exploration", ge=0.0, le=100.0)

class AssessmentParameters(BaseModel):
    posterior_probability_for_credible_intervals: float = Field(
        95.0, description="Posterior probability used for computing credible intervals in assessment")
    posterior_probability_for_winner: float = Field(
        99.0, description="Minimum value of posterior probability of being the best version which needs to be attained by a version to be declared winner")

class RollForwardStrategy(str, Enum):
    probabilistic = "Probabilistic" # rollforward to a candidate if its win probability is above posterior_probability_for_winner else rollback to baseline
    greedy = "Greedy" # Ignore probabilities. Rollback to the greedily choosen best version

class AdvancedParameters(BaseModel):
    step_size: float = Field(
        1.0, description="Maximum possible increment in a candidate's traffic during the initial phase of the experiment", ge=0.0, le=100.0)
    max_iterations: int = Field(100, description = "Maximum number of iterations in this experiment")
    traffic_control: TrafficControlParameters = Field(None, description = "Advanced traffic control parameters")
    assessment: AssessmentParameters = Field(None, description = "Advanced assessment parameters")
    rollforward_strategy: RollForwardStrategy = Field(RollForwardStrategy.probabilistic, description = "Strategy to use for rolling forward")

# parameters for current iteration of experiment
class ExperimentIterationParameters(BaseModel):
    start_time: datetime = Field(...,
                                 description="Start time of the experiment")
    iteration_number: int = Field(..., description = "Iteration number, ranging from 1 to maximum number of iterations (advanced_parameters.max_iterations)", ge = 1)
    service_name: str = Field(..., description = "Name of the service in this experiment")
    baseline: Version = Field(..., description="The baseline version")
    candidates: Sequence[Version] = Field(...,
                                          description="The set of candidates")
    metric_specs: MetricSpecs = Field(
        ..., description="All metric specification")
    criteria: Sequence[Criterion] = Field(
        ..., description="Criteria to be assessed for each version in this experiment")
    advanced_parameters: AdvancedParameters = Field(
        None, description = "Advanced parameters")
    current_traffic_split: Dict[Union[int, str, UUID], float] = Field(None, description="Current traffic split across versions")
    last_state: Any = Field(
        None, description="Last recorded state from analytics service")
