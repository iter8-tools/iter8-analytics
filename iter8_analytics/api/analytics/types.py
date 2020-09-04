"""
Module containing pydantic data models for iter8 along with some global constants
"""
# core python dependencies
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Tuple, Union, Sequence, Iterable, Dict, Any, List, Optional

# external module dependencies
from pydantic import BaseModel, Field

# type alias
iter8id = Union[int, str, UUID]

# Types pertaining to experiment iteration requests


class Version(BaseModel):
    id: iter8id = Field(..., description="ID of the version")
    version_labels: dict = Field(
        ..., description="Key-value pairs used in prometheus queries to achieve version level grouping")


class DirectionEnum(str, Enum):  # directions for metric values
    lower = "lower"
    higher = "higher"


class MetricSpec(BaseModel):
    id: iter8id = Field(..., alias="name", description="ID of the metric")
    preferred_direction: DirectionEnum = Field(
        None, description="Indicates preference for metric values -- lower, higher, or None (default)")
    # this will be used in KUI / Kiali / controller status fields
    descriptive_short_name: str = Field(
        None, description="Descriptive short name")

    class Config:
        allow_population_by_field_name = True

# counter metric defined in iter8 configmaps


class CounterMetricSpec(MetricSpec):
    query_template: str = Field(...,
                                description="Prometheus query template")


# ratio metric = numerator counter / denominator counter
class RatioMetricSpec(MetricSpec):
    numerator: str = Field(
        ..., description="ID of the counter metric used in numerator")
    denominator: str = Field(
        ..., description="ID of the counter metric used in denominator")
    zero_to_one: bool = Field(
        False, description="Boolean flag indicating if the value of this metric is always in the range 0 to 1")


class MetricSpecs(BaseModel):
    counter_metrics: Sequence[CounterMetricSpec] = Field(
        ..., description="All counter metric specs")
    ratio_metrics: Sequence[RatioMetricSpec] = Field(
        ..., description="All ratio metric specs")


class ThresholdEnum(str, Enum):
    absolute = "absolute"  # this threshold represents an absolute limit
    relative = "relative"  # this threshold represents a limit relative to baseline


class Threshold(BaseModel):
    threshold_type: ThresholdEnum = Field(...,
                                          alias="type", description="Type of threshold")
    value: float = Field(..., description="Value of threshold")

    class Config:
        allow_population_by_field_name = True


class Criterion(BaseModel):
    id: iter8id = Field(..., description="ID of the criterion")
    metric_id: iter8id = Field(
        ..., description="ID of the metric. This matches the unique ID of the metric in the metric spec")
    is_reward: bool = Field(
        False, description="Boolean flag indicating if this metric will be used as reward to be optimized in an A/B test. Only ratio metrics can be used as a reward. At most one metric can be used as reward")
    threshold: Threshold = Field(
        None, description="Threshold value for this metric if any")


class TrafficSplitStrategy(str, Enum):
    progressive = "progressive"  # PBR
    top_2 = "top_2"  # top 2 PBR
    uniform = "uniform"  # Uniform split


class TrafficControl(BaseModel):  # parameters pertaining to traffic control
    max_increment: float = Field(
        2.0, description="Maximum possible increment in a candidate's traffic during the initial phase of the experiment", ge=0.0, le=100.0)
    strategy: TrafficSplitStrategy = Field(
        TrafficSplitStrategy.progressive, description="Traffic split algorithm to use during the experiment")


class StatusEnum(str, Enum):
    all_ok = "all_ok"
    no_last_state = "no_last_state"
    no_prom_server = "no_prom_server"
    no_prom_data = "no_prom_data"
    # needs to be refined
    insufficient_data_for_assessment = "insufficient_data_for_assessment"
    invalid_experiment_spec = "invalid_experiment_spec"  # needs to be refined
    invalid_query_template = "invalid prometheus query template"
    absent_version_in_prom_response = "absent version in prometheus response"
    no_versions_in_prom_response = "no versions in prometheus response"
    zeroed_counter = "zeroed counter"
    zeroed_ratio = "zeroed ratio"
    nan_value = "nan value"
    uninitialized_belief = "uninitialized belief"
    uninitialized_value = "uninitialized value"

# Types pertaining to metrics


class DataPoint(BaseModel):
    """A single data point for a given metric and version.
    """
    value: float = Field(None, description="Value of the metric")
    timestamp: datetime = Field(
        None, description="Time at which this metric was last queried and updated")
    status: StatusEnum = Field(
        StatusEnum.all_ok, description="Status of this data point derived from prometheus response")


class CounterDataPoint(DataPoint):
    """A single counter data point for a given counter metric and version.
    """


class RatioDataPoint(DataPoint):
    """A single ratio data point for a given ratio metric and version.
    """


class AggregatedCounterDataPoint(CounterDataPoint):
    """A single aggregated counter data point for a given metric and version.
    """


class AggregatedRatioDataPoint(RatioDataPoint):
    """A single aggregated ratio data point for a given metric and version.
    """


class RatioMaxMin(BaseModel):
    minimum: float = Field(
        None,  description="minimum observed value of a ratio metric")
    maximum: float = Field(
        None,  description="maximum observed value of a ratio metric")

# End of types pertaining to metrics. Back to experiment iteration request


class LastState(BaseModel):  # last state recorded by analytics service in its previous response
    aggregated_counter_metrics: Dict[iter8id, Dict[iter8id, AggregatedCounterDataPoint]] = Field(
        None, description="Dictionary mapping from version id to another dictionary which maps from counter metric id to its latest aggregated metric value")
    aggregated_ratio_metrics: Dict[iter8id, Dict[iter8id, AggregatedRatioDataPoint]] = Field(
        None, description="Dictionary mapping from version id to another dictionary which maps from ratio metric id to its latest aggregated metric value")
    ratio_max_mins: Dict[iter8id, RatioMaxMin] = Field(
        None, description="Dictionary mapping from ratio metric id to its max min values")
    traffic_split_recommendation: Dict[TrafficSplitStrategy, Dict[iter8id, int]] = Field(
        None, description="Traffic split recommendation on a per algorithm basis. Each recommendation contains the percentage of traffic on a per-version basis in the inner dict")
    # this is a dictionary which maps version ids to percentage of traffic allocated to them. The percentages need to add up to 100

# parameters for current iteration of experiment


class ExperimentIterationParameters(BaseModel):
    start_time: datetime = Field(...,
                                 description="Start time of the experiment")
    iteration_number: int = Field(
        None, description="Iteration number. This is mandatory for controller interactions. Optional for human-in-the-loop interactions", ge=0)
    service_name: str = Field(...,
                              description="Name of the service in this experiment")
    baseline: Version = Field(..., description="The baseline version")
    candidates: Sequence[Version] = Field(...,
                                          description="The set of candidates")
    metric_specs: MetricSpecs = Field(
        ..., description="All metric specification")
    criteria: Sequence[Criterion] = Field(
        ..., description="Criteria to be assessed for each version in this experiment")
    traffic_control: TrafficControl = Field(TrafficControl(
        max_increment=2.0, strategy=TrafficSplitStrategy.progressive
    ), description="Traffic control parameters")  # default traffic control
    last_state: LastState = Field(
        None, description="Last recorded state from analytics service")


class QuerySpec(BaseModel):
    """Base class for prometheus query spec
    """
    version_label_keys: Iterable[str]  # prometheus label names (for grouping)
    start_time: datetime  # start time for computing duration in the query


class CounterQuerySpec(QuerySpec):
    """Base class for prometheus counter query spec
    """
    query_template: Any

    class Config:
        arbitrary_types_allowed = True


class RatioQuerySpec(QuerySpec):
    """Base class for prometheus ratio query spec
    """
    numerator_template: Any
    denominator_template: Any

    class Config:
        arbitrary_types_allowed = True

# Types pertaining to experiment iteration response


class Interval(BaseModel):
    lower: float = Field(..., description="Lower endpoint of the interval")
    upper: float = Field(..., description="Upper endpoint of the interval")


class RatioStatistics(BaseModel):
    improvement_over_baseline: Interval = Field(
        None, description="Credible interval for percentage improvement over baseline. Defined only for non-baseline versions. This is currently computed based on Bayesian estimation")
    probability_of_beating_baseline: float = Field(
        None, le=1.0, ge=0.0, description="Probability of beating baseline with respect to this metric. Defined only for non-baseline versions. This is currently computed based on Bayesian estimation")
    probability_of_being_best_version: float = Field(
        None, le=1.0, ge=0.0, description="Probability of being the best version with respect to this metric. This is currently computed based on Bayesian estimation")
    credible_interval: Interval = Field(
        ..., description="Credible interval for the value of this metric. This is currently computed based on Bayesian estimation")


class Statistics(BaseModel):
    value: float = Field(None, description="Current value of this metric")
    ratio_statistics: RatioStatistics = Field(
        None, description="Additional statistics. Defined only for ratio metrics")


class ThresholdAssessment(BaseModel):
    threshold_breached: bool = Field(
        ..., description="True if threshold is breached. False otherwise")
    probability_of_satisfying_threshold: Optional[float] = Field(
        None, le=1.0, ge=0.0, description="Probability of satisfying the threshold. Defined only for ratio metrics. This is currently computed based on Bayesian estimation")


class CriterionAssessment(BaseModel):  # assessment per criterion per version
    id: str = Field(..., description="ID of the criterion")
    metric_id: str = Field(..., description="ID of the metric")
    # name: str = Field(..., description="Name of the metric")
    # is_counter: bool = Field(..., description = "Is this a counter metric?")
    # lower_is_better: bool = Field(True, description =  "Are lower values of this metric better?")
    statistics: Statistics = Field(...,
                                   description="Statistics for this metric")
    threshold_assessment: ThresholdAssessment = Field(
        None, description="Assessment of how well this metric is doing with respect to threshold. Defined only for metrics with a threshold")


class VersionAssessment(BaseModel):  # assessment per version
    id: str = Field(..., description="ID of the version")
    # e.g. keys within tags: destination_service_namespace and destination_workload
    # tags: Dict[str, str] = Field(..., description="Tags for this version")
    # baseline: bool = Field(False, description = "Is this the baseline?")
    request_count: int = Field(
        None, ge=0, description="Number of requests sent to this version until now")
    criterion_assessments: List[CriterionAssessment] = Field(
        ..., description="Metric assessments for this version")
    win_probability: float = Field(
        ..., description="Posterior probability of this version. This is currently computed based on Bayesian estimation")


# assessment per candidate
class CandidateVersionAssessment(VersionAssessment):
    rollback: bool = Field(
        False, description="Rollback this version. Currently candidates can be rolled back if they violate criteria for which rollback_on_violation is True")


class WinnerAssessment(BaseModel):
    winning_version_found: bool = Field(
        ..., description="Indicates whether or not a clear winner has emerged. This is currently computed based on Bayesian estimation and uses posterior_probability_for_winner from the iteration parameters")
    current_best_version: str = Field(
        ..., description="ID of the current best version with the maximum probability of winning. This is currently computed based on Bayesian estimation")
    probability_of_winning_for_best_version: float = Field(
        ..., description="Posterior probability of the current best version. This is currently computed based on Bayesian estimation")
   # coming soon
    # safe_to_rollforward: bool = Field(False, description = "True if it is now safe to terminate the experiment early and rollforward to the winner")


class Iter8AssessmentAndRecommendation(BaseModel):
    timestamp: datetime = Field(...,
                                description="Timestamp at which the current assessment and recommendation is created")
    baseline_assessment: VersionAssessment = Field(
        ..., description="Baseline's assessment")
    candidate_assessments: List[CandidateVersionAssessment] = Field(
        ..., description="Assessment  of candidate versions")
    traffic_split_recommendation: Dict[TrafficSplitStrategy, Dict[iter8id, int]] = Field(
        ..., description="Traffic split recommendation on a per algorithm basis. Each recommendation contains the percentage of traffic on a per-version basis in the inner dict")
    # this is a dictionary which maps version ids to percentage of traffic allocated to them. The percentages need to add up to 100
    winner_assessment: WinnerAssessment = Field(
        ..., description="Assessment summary for winning candidate. This is currently computed based on Bayesian estimation")
    status: List[StatusEnum] = Field(
        [StatusEnum.all_ok], description="List of status codes for this iteration -- did this iteration run without exceptions and if not, what went wrong?")
    status_interpretations: Dict[str, str] = Field({
        StatusEnum.all_ok: "Data from Prometheus available and was utilized without a glitch during this iteration",
        StatusEnum.no_last_state: "No last state available during this iteration",
        StatusEnum.no_prom_server: "Prometheus server unavailable",
        StatusEnum.no_prom_data: "Incomplete Prometheus data during this iteration",
        StatusEnum.insufficient_data_for_assessment: "Insufficient data available to create an assessment",
        StatusEnum.invalid_experiment_spec: "Invalid experiment specification",
        StatusEnum.invalid_query_template: "Invalid query template",
        StatusEnum.absent_version_in_prom_response: "This version is absent in prom response",
        StatusEnum.no_versions_in_prom_response: "No versions are present in prom response",
        StatusEnum.zeroed_counter: "Using the default zero value for counter metric",
        StatusEnum.zeroed_ratio: "Using the default zero value for ratio metric",
        StatusEnum.nan_value: "NaN ratio value",
        StatusEnum.uninitialized_belief: "Uninitialized belief",
        StatusEnum.uninitialized_value: "Uninitialized value"
    },
        description="Human-friendly interpretations of the status codes returned by the analytics service")  # the index of an interpretation corresponds to the corresponding status enum
    last_state: Dict[str, Any] = Field(
        None, description="Last recorded state from analytics service")

# These are not pydantic models, simply advanced iter8 parameters defined globally


class AdvancedParameters:
    # 5% of traffic always used for exploration
    exploration_traffic_percentage = 5.0
    posterior_probability_for_credible_intervals = 0.95
    # no winner until iter8 is 99% confident
    min_posterior_probability_for_winner = 0.99
    # a higher value of this factor encourages greater exploration
    variance_boost_factor = 1.0
