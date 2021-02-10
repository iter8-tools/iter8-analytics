"""
Module containing pydantic data models for iter8 v2
"""
# core python dependencies
from typing import Sequence, Dict, Union
from datetime import datetime
from enum import Enum
from decimal import Decimal

# external module dependencies
from pydantic import BaseModel, Field, conlist

# iter8 dependencies
from iter8_analytics.api.utils import convert_to_float, convert_to_quantity

PolymorphicQuantity = Union[int, str, float]

class VersionVariables(BaseModel):
    """
    Pydantic model for Version variables
    """
    name: str = Field(..., description = "version variable name")
    value: str = Field(..., description= "version variable value")

class Version(BaseModel):
    """
    Pydantic model for Version
    """
    name: str = Field(..., description = "version name")
    variables: Sequence[VersionVariables] = Field(None, descriptiopn = "version tags (key-value pairs)")

class VersionInfo(BaseModel):
    """
    Pydantic model for versionInfo field in experiment spec subresource
    """
    baseline: Version = Field(..., description = "baseline version")
    candidates: Sequence[Version] = Field(None, description = "a list of candidate versions")

class PreferredDirection(str, Enum):
    """
    Preferred directions for a metric
    """
    high = "High"
    low = "Low"

class Reward(BaseModel):
    """
    Pydantic model for reward metric
    """
    metric: str = Field(..., description = "name of the reward metric", min_length = 1)
    preferredDirection: PreferredDirection = Field(..., \
        description = "preferred direction for this metric")

class Objective(BaseModel):
    """
    Pydantic model for experiment objective
    """
    metric: str = Field(..., description = "metric name")
    upperLimit: PolymorphicQuantity = Field(None, description = "upper limit for the metric")
    lowerLimit: PolymorphicQuantity = Field(None, description = "lower limit for the metric")

    def convert_to_float(self):
        """
        Apply convert_to_float on upper and lower limits
        """
        self.upperLimit = convert_to_float(self.upperLimit)
        self.lowerLimit = convert_to_float(self.lowerLimit)
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantity on upper and lower limits
        """
        self.upperLimit = convert_to_quantity(self.upperLimit)
        self.lowerLimit = convert_to_quantity(self.lowerLimit)
        return self

class Criteria(BaseModel):
    """
    Pydantic model for Criteria field in experiment spec
    """
    reward: Reward = Field(None, description = "reward metric")
    objectives: Sequence[Objective] = Field(None, description = "sequence of objectives")

    def convert_to_float(self):
        """
        Apply convert_to_float on objectives
        """
        if self.objectives is not None:
            self.objectives = [obj.convert_to_float() for obj in self.objectives]
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on objectives
        """
        if self.objectives is not None:
            self.objectives = [obj.convert_to_quantity() for obj in self.objectives]
        return self

class ExperimentTestingPattern(str, Enum):
    """
    Experiment testing patterns
    """
    canary = "Canary"
    ab = "A/B"
    abn = "A/B/N"
    conformance = "Conformance"
    

class ExperimentDeploymentPattern(str, Enum):
    """
    Algorithm deployment patterns
    """
    progressive = "Progressive"
    fixed = "FixedSplit"
    bluegreen = "BlueGreen"

class WeightsConfig(BaseModel):
    """
    Pydantic model for weights configuration in experiment spec
    """
    maxCandidateWeight: int = Field(100, description = "units = percent; \
        candidate weight never exceeds this value", le = 100, ge = 0)
    maxCandidateWeightIncrement: int = Field(5, description = "units = percent; \
        candidate weight increment never exceeds this value", le = 100, ge = 0)
    

class ExperimentStrategy(BaseModel):
    """
    Experiment strategy
    """
    testingPattern: ExperimentTestingPattern = Field(..., \
        description="indicates preference for metric values -- lower, higher, or None (default)")
    deploymentPattern: ExperimentDeploymentPattern = Field(ExperimentDeploymentPattern.progressive, description = \
        "weight computation algorithm")
    weights: WeightsConfig = Field(None, \
        description = "weights configuration")

class MetricSpec(BaseModel):
    """
    Pydantic model for metric spec subresource
    """
    params: Dict[str, str] = Field(None, description = "parameters to be used \
        as part of the REST query for this metric")
    provider: str = Field(..., description = "identifier for the metrics backend")

class MetricObject(BaseModel):
    """
    Pydantic model for metricObj subresource
    """
    spec: MetricSpec = Field(..., description = "metrics resource spec")


class MetricResource(BaseModel):
    """
    Pydantic model for metric resource
    """
    name: str = Field(..., description= "name of the metric")
    metricObj: MetricObject = Field(..., description = "metric obj resource")
    
class ExperimentSpec(BaseModel):
    """
    Pydantic model for experiment spec subresource
    """
    strategy: ExperimentStrategy = Field(..., \
        description = "experiment strategy")
    versionInfo: VersionInfo = Field(..., description = "versions in the experiment")
    criteria: Criteria = Field(None, description = "experiment criteria")
    metrics: Sequence[MetricResource] = Field(None, description = "Sequence of \
        MetricResource objects")

    def convert_to_float(self):
        """
        Apply convert_to_float on criteria
        """
        if self.criteria is not None:
            self.criteria = self.criteria.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on criteria
        """
        if self.criteria is not None:
            self.criteria = self.criteria.convert_to_quantity()
        return self

class VersionMetric(BaseModel):
    """
    Pydantic model for a version metric object
    """
    max: PolymorphicQuantity = Field(None, description = "maximum observed value \
        for this metric for this version")
    min: PolymorphicQuantity = Field(None, description = "minimum observed value \
        for this metric for this version")
    value: PolymorphicQuantity = Field(None, description = "last observed value \
        for this metric for this version")
    sample_size: PolymorphicQuantity = Field(None, description = "last observed value \
        for the sample_size metric for this version; this is none if sample_size is not specified")

    def convert_to_float(self):
        """
        Apply convert_to_float on all fields
        """
        self.max = convert_to_float(self.max)
        self.min = convert_to_float(self.min)
        self.value = convert_to_float(self.value)
        self.sample_size = convert_to_float(self.sample_size)
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on all fields
        """
        self.max = convert_to_quantity(self.max)
        self.min = convert_to_quantity(self.min)
        self.value = convert_to_quantity(self.value)
        self.sample_size = convert_to_quantity(self.sample_size)
        return self

class AggregatedMetric(BaseModel):
    """
    Pydantic model for an aggregated metric object
    """
    max: PolymorphicQuantity = Field(None, description = "maximum observed value for this metric")
    min: PolymorphicQuantity = Field(None, description = "minimum observed value for this metric")
    # min_items == 1 since at least one version (baseline) will be present
    data: Dict[str, VersionMetric] = Field(..., \
        description = "dictionary with version names as keys and VersionMetric objects as values")

    def convert_to_float(self):
        """
        Apply convert_to_float on min, max, and each version metric
        """
        self.max = convert_to_float(self.max)
        self.min = convert_to_float(self.min)
        for key, value in self.data.items():
            self.data[key] = value.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on min, max, and each version metric
        """
        self.max = convert_to_quantity(self.max)
        self.min = convert_to_quantity(self.min)
        for key, value in self.data.items():
            self.data[key] = value.convert_to_quantity()
        return self

class AggregatedMetrics(BaseModel):
    """
    Pydantic model for aggregated metrics response
    """
    data: Dict[str, AggregatedMetric] = Field(..., \
    description = "dictionary with metric names as keys and AggregatedMetric objects as values")
    message: str = Field(None, description = "human-readable description of aggregated metrics")

    def convert_to_float(self):
        """
        Apply convert_to_float on each aggregated metric
        """
        for key, value in self.data.items():
            self.data[key] = value.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on each aggregated metric
        """
        for key, value in self.data.items():
            self.data[key] = value.convert_to_quantity()
        return self

class VersionAssessments(BaseModel):
    """
    Pydantic model for version assessments
    """
    data: Dict[str, Sequence[bool]] = Field(..., \
    description = "dictionary with version name as key and sequence of booleans as value; each element of the sequence indicates if the version satisfies the corresponding objective.")
    message: str = Field(None, description = "human-readable description of version assessments")

class WinnerAssessmentData(BaseModel):
    """
    Pydantic model for winner assessment data
    """
    winnerFound: bool = Field(False, description = "boolean value indicating if winner is found")
    winner: str = Field(None, description = "winning version; None if winner not found")
    bestVersions: Sequence[str] = Field([], description = "the list of best versions found; if this list is a singleton, then winnerFound = true and winner is the only element of the list")

class WinnerAssessment(BaseModel):
    """
    Pydantic model for winner assessment
    """
    data: WinnerAssessmentData = Field(WinnerAssessmentData(), description = \
        "winner assessment data")
    message: str = Field(None, description = "explanation for winning version")

class VersionWeight(BaseModel):
    """
    Pydantic model for version weight
    """
    name: str = Field(..., description = "version name")
    value: int = Field(..., description = "weight for a version", ge = 0)

class Weights(BaseModel):
    """
    Pydantic model for weight object
    """
    # number of entries in data equals number of versions in the experiment
    data: Sequence[VersionWeight] = Field(..., description = \
        "weights for versions")
    message: str = Field(None, description = "human-readable description for weights")

class Analysis(BaseModel):
    """
    Pydantic model for analysis section of experiment status
    """
    aggregatedMetrics: AggregatedMetrics = Field(None, \
        description = "aggregated metrics")
    versionAssessments: VersionAssessments = Field(None, \
        description = "version assessments")
    winnerAssessment: WinnerAssessment = Field(None, \
        description = "winner assessment")
    weights: Weights = Field(None, description = "weight recommendations")

    def convert_to_float(self):
        """
        Apply convert_to_float on aggregatedMetric
        """
        if self.aggregatedMetrics is not None:
            self.aggregatedMetrics = self.aggregatedMetrics.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on aggregatedMetric
        """
        if self.aggregatedMetrics is not None:
            self.aggregatedMetrics = self.aggregatedMetrics.convert_to_quantity()
        return self

class ExperimentStatus(BaseModel):
    """
    Pydantic model for experiment status subresource
    """
    startTime: datetime = Field(..., description = "starttime of the experiment")
    analysis: Analysis = Field(None, description = "currently available analysis")
    currentWeightDistribution: Sequence[VersionWeight] = Field(None, \
        description = "current weight distribution for versions")

    def convert_to_float(self):
        """
        Apply convert_to_float on spec and status
        """
        if self.analysis is not None:
            self.analysis = self.analysis.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on spec and status
        """
        if self.analysis is not None:
            self.analysis = self.analysis.convert_to_quantity()
        return self

class ExperimentResource(BaseModel):
    """
    Pydantic model for experiment resource
    """
    spec: ExperimentSpec = Field(..., description = "experiment spec subresource")
    status: ExperimentStatus = Field(..., description = "experiment status subresource")

    def convert_to_float(self):
        """
        Apply convert_to_float on spec and status
        """
        self.spec = self.spec.convert_to_float()
        self.status = self.status.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on spec and status
        """
        self.spec = self.spec.convert_to_quantity()
        self.status = self.status.convert_to_quantity()
        return self
