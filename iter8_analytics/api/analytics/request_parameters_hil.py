"""
Specification of the request parameters for the REST API code related to analytics.
"""

from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import List, Tuple
####
# Schema of the request body with the parameters for
# POST /experiment/<algorithm-name>
####

#Questions/Comments:
# 1. How do I set example values that will be available to the user in Swagger UI
# 2. Reward Criterion is same as Criterion
# 3. Go over the comments on the git issue
# 4. Confidence gt, lt values?
# 5. Named tuples for belief distributions has been removed
# 6. Should I validate Last State or let it be a raw dictionary as was the case in our prevous design?

class VersionDefinition(BaseModel):
    """
    Create an item with all the information:

    - **start_time**: ISO8601 timestamp for the beginning of the time range of interest
    - **end_time**: ISO8601 timestamp for the end of the time range of interest; if omitted, current time is assumed
    - **tags**: Key-value pairs identifying the data pertaining to a version
    """
    start_time: datetime = Field(..., description="ISO8601 timestamp for the beginning of the time range of interest")
    end_time: datetime = Field(None, description="ISO8601 timestamp for the end of the time range of interest; if omitted, current time is assumed")
    tags: dict = Field(..., description="Key-value pairs identifying the data pertaining to a version")

class MinMax(BaseModel):
    """
    - **min**: Minimum possible value of the metric
    - **max**: Maximum possible value of the metric
    """
    min: float = Field(..., description="Minimum possible value of the metric")
    max: float = Field(..., description="Maximum possible value of the metric")

class CriterionEnum(str, Enum):
    delta = 'delta'
    threshold = 'threshold'

class Criterion(BaseModel):
    """
    - **metric_name**: Name of the metric to which the criterion applies
    - **is_counter**: Describles the type of metric. Options: "True": Metrics which are cumulative in nature and represent monotonically increasing values
    - **absent_value**: Describes what value should be returned if Prometheus did not find any data corresponding to the metric
    - **metric_query_template**: Prometheus Query of the metric to which the criterion applies
    - **metric_sample_size_query_template**: Sample Size Query for the metric to which the criterion applies
    - **min_max**: The minimum and maximum possible value of the metric, if available
    """
    metric_name: str = Field(..., description='Name of the metric to which the criterion applies')
    is_counter: bool = Field(..., description='Describles the type of metric. Options: "True": Metrics which are cumulative in nature and represent monotonically increasing values')
    absent_value: str = Field(None, description='Describes what value should be returned if Prometheus did not find any data corresponding to the metric')
    metric_query_template: str = Field(..., description='Prometheus Query of the metric to which the criterion applies')
    metric_sample_size_query_template: str = Field(..., description='Sample Size Query for the metric to which the criterion applies')
    min_max: MinMax = None = Field(None, description='The minimum and maximum possible value of the metric, if available')

class SuccessCriterion(Criterion):
    """
    - **type**: Criterion type. Options: "delta": compares the candidate against the baseline version with respect to the metric; "threshold": checks the candidate with respect to the metric
    - **value**: Value to be check against
    - **stop_on_failure**: Indicates whether or not the experiment must finish if this criterion is not satisfied; defaults to false
    """
    type: CriterionEnum = Field(..., description='Criterion type. Options: "delta": compares '
        'the candidate against the baseline version with respect to the metric; "threshold": '
        'checks the candidate with respect to the metric')
    value: float = Field(..., description='Value to be check against')
    stop_on_failure: bool = Field(False, description='Indicates whether or not the experiment '
        'must finish if this criterion is not satisfied; defaults to false')


class TrafficControlDefault(BaseModel):
    max_traffic_percentage: float = Field(50, description='Maximum percentage of traffic that the candidate version '
        'will receive during the experiment; defaults to 50%', gt=0.0)
    success_criteria: List[SuccessCriterion] = Field(..., description='List of criteria for assessing the candidate version',
        min_items=1)
    reward: Criterion = Field(None, description="Reward attribute to maximize in the A/B test")

class TrafficControlCheckAndIncrement(TrafficControlDefault):
    step_size: float = Field(2.0, description='Increment (in percent points) to be applied to the '
        'traffic received by the candidate version each time it passes the '
        'success criteria; defaults to 1 percent point', gt=1.0)


class TrafficControlBayesianRouting(TrafficControlDefault):
    confidence: float = Field(0.95, gt=0.0, lt=1, description='Posterior probability that all success criteria is met')
    reward: Criterion = Field(None, description='Reward attribute to maximize in the A/B test')

class VersionLastStateDefault(BaseModel):
    traffic_percentage: float = Field(..., description="Percentage of traffic to this version")
    success_criterion: List[tuple] = Field(..., description='List of success criterion results from the previous iteration '
        'for this version')

class VersionLastStateBayesianRouting(BaseModel):
    success_criterion_belief: List[Tuple[float, float, float, float]] = Field(..., description='The belief distribution of each '
        'success criterion metric')
    reward_belief: Tuple[float, float, float, float] = Field(..., description="The belief distribution of the reward metric")

class LastStateDefault(BaseModel):
    baseline: VersionLastStateDefault = Field({"traffic_percentage": 100, "success_criterion": []}, description='Baseline traffic and successcriterion information for the '
        'previous iteration')
    candidate: VersionLastStateDefault = Field({"traffic_percentage": 0, "success_criterion": []}, description='Candidate traffic and successcriterion information for the '
        'previous iteration')
    change_observed: bool = Field(False, description='Will always take False at the beginning of the iteration')


class LastStateEpsilonTGreedy(LastStateDefault):
    effective_iteration_count: int = Field(0, description='Count of the number of times traffic was updated '
        'in this experiment')

class LastStateBayesianRouting(BaseModel):
    baseline: VersionLastStateBayesianRouting = Field({"success_criterion_belief": [], "reward_belief": [None, None, None, None]})
    candidate: VersionLastStateBayesianRouting = Field({"success_criterion_belief": [], "reward_belief": [None, None, None, None]})


class RequestParametersDefault(BaseModel):
    baseline: VersionDefinition = Field(..., description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the baseline version')
    candidate: VersionDefinition = Field(..., description='Specifies a time interval and key-value pairs for '
        'retrieving and processing data pertaining to the candidate version')

class RequestParametersCheckAndIncrement(RequestParametersDefault):

    traffic_control: TrafficControlCheckAndIncrement = Field(..., description='Parameters controlling the behavior of the analytics')
    last_state: LastStateDefault = Field(..., description='State returned by the server on the previous call')

class RequestParametersEpsilonTGreedy(RequestParametersDefault):
    traffic_control: TrafficControlDefault = Field(..., description='Parameters controlling the behavior of the analytics')
    last_state: LastStateEpsilonTGreedy = Field(..., description='State returned by the server on the previous call')

class RequestParametersBayesianRouting(RequestParametersDefault):
    traffic_control: TrafficControlBayesianRouting = Field(..., description='Parameters controlling the behavior of the analytics')
    last_state: LastStateBayesianRouting = Field(..., description='State returned by the server on the previous call')
