"""
Module containing pydantic data models for iter8 v2
"""
# core python dependencies
from typing import Sequence, Dict, Union
from datetime import datetime
from enum import Enum

# external module dependencies
from pydantic import BaseModel, Field

# iter8 dependencies
from iter8_analytics.api.utils import convert_to_float, convert_to_quantity

PolymorphicQuantity = Union[int, str, float]

#### Common

class NamedValue(BaseModel):
    """
    Pydantic model for a name-value pair.
    """
    name: str = Field(..., description = "name")
    value: str = Field(..., description= "value")

#### Metrics

class AuthType(str, Enum):
    """
    Types of authentication used in the HTTP(S) request to the metrics API endpoint.
    """
    BASIC = "Basic"
    BEARER = "Bearer"
    APIKEY = "APIKey"

class Method(str, Enum):
    """
    The request method (aka verb) used in the HTTP(s) request to the metrics API endpoint.
    """
    GET = "GET"
    POST = "POST"

class MetricSpec(BaseModel):
    """
    Pydantic model for metric spec subresource
    """
    params: Sequence[NamedValue] = Field(None, description = "parameters to be used \
        as part of the REST query for this metric")
    provider: str = Field(None, description = "identifier for the metrics backend")
    jqExpression: str = Field(..., \
        description = "jq expression used for unmarshaling metric value from \
            the JSON response body of the metrics backend's REST API")
    urlTemplate: str = Field(..., description = \
        "template of the URL to be used for querying this metric")
    authType: AuthType = Field(None, description = \
        "type of authentication used in the HTTP(S) request to the metrics API endpoint")
    method: Method = Field(Method.GET, description = \
        "HTTP method used in the HTTP(S) request to the metrics API endpoint")
    secret: str = Field(None, description="k8s secret reference in the namespace/name format")
    body: str = Field(None, description="body of the HTTP(S) request; \
        this field is relevant only if method is POST")
    headerTemplates: Sequence[NamedValue] = Field(None, \
        description = "headerTemplates are field names \
        and value templates for headers that should be passed to the metrics backend; \
        typically, these are authentication headers; \
        values are interpolated using secret data")

class MetricResource(BaseModel):
    """
    Pydantic model for metric resource object
    """
    spec: MetricSpec = Field(..., description = "metrics resource spec")

#### Experiments

class VersionDetail(BaseModel):
    """
    Pydantic model for VersionDetail
    """
    name: str = Field(..., description = "version name")
    variables: Sequence[NamedValue] = \
        Field(None, description = "version tags (key-value pairs)")

class VersionInfo(BaseModel):
    """
    Pydantic model for versionInfo field in experiment spec subresource
    """
    baseline: VersionDetail = Field(..., description = "baseline version")
    candidates: Sequence[VersionDetail] = Field(None, description = "a list of candidate versions")

class PreferredDirection(str, Enum):
    """
    Preferred directions for a metric
    """
    HIGH = "High"
    LOW = "Low"

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
    upper_limit: PolymorphicQuantity = Field(None, \
        description = "upper limit for the metric", alias = "upperLimit")
    lower_limit: PolymorphicQuantity = Field(None, \
        description = "lower limit for the metric", alias = "lowerLimit")

    def convert_to_float(self):
        """
        Apply convert_to_float on upper and lower limits
        """
        self.upper_limit = convert_to_float(self.upper_limit)
        self.lower_limit = convert_to_float(self.lower_limit)
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantity on upper and lower limits
        """
        self.upper_limit = convert_to_quantity(self.upper_limit)
        self.lower_limit = convert_to_quantity(self.lower_limit)
        return self

class Criteria(BaseModel):
    """
    Pydantic model for Criteria field in experiment spec
    """
    rewards: Sequence[Reward] = Field(None, description = "sequence of rewards")
    objectives: Sequence[Objective] = Field(None, \
        description = "sequence of metric-based objectives")

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

class TestingPattern(str, Enum):
    """
    Experiment testing patterns
    """
    CANARY = "Canary"
    AB = "A/B"
    ABN = "A/B/N"
    CONFORMANCE = "Conformance"

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
    testingPattern: TestingPattern = Field(..., \
        description="indicates preference for metric values -- lower, higher, or None (default)")
    weights: WeightsConfig = Field(None, description = "weights configuration")

class MetricInfo(BaseModel):
    """
    Pydantic model for metric resource
    """
    name: str = Field(..., description= "name of the metric")
    metricObj: MetricResource = Field(..., description = "metric resource object")

class ExperimentSpec(BaseModel):
    """
    Pydantic model for experiment spec subresource
    """
    strategy: ExperimentStrategy = Field(..., \
        description = "experiment strategy")
    versionInfo: VersionInfo = Field(..., description = "versions in the experiment")
    criteria: Criteria = Field(None, description = "experiment criteria")

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
        for the sampleSize metric for this version; equals None if sampleSize is not specified", alias = "sampleSize")

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

class AggregatedMetricsAnalysis(BaseModel):
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

class VersionAssessmentsAnalysis(BaseModel):
    """
    Pydantic model for version assessments
    """
    data: Dict[str, Sequence[bool]] = Field(..., \
    description = "dictionary with version name as key and \
        sequence of booleans as value; each element of the sequence indicates if \
        the version satisfies the corresponding objective.")
    message: str = Field(None, description = "human-readable description of version assessments")

class WinnerAssessmentData(BaseModel):
    """
    Pydantic model for winner assessment data
    """
    winnerFound: bool = Field(False, description = "boolean value indicating if winner is found")
    winner: str = Field(None, description = "winning version; None if winner not found")
    bestVersions: Sequence[str] = Field([], \
        description = "the list of best versions found; \
        if this list is a singleton, then winnerFound = true \
        and winner is the only element of the list")

class WinnerAssessmentAnalysis(BaseModel):
    """
    Pydantic model for winner assessment
    """
    data: WinnerAssessmentData = Field(WinnerAssessmentData(), description = \
        "winner assessment data")
    message: str = Field(None, description = "explanation for winning version")

class VersionWeight(BaseModel):
    """
    Pydantic model for version weight.
    """
    name: str = Field(..., description = "version name")
    value: int = Field(..., description = "weight for a version", ge = 0)

class WeightsAnalysis(BaseModel):
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
    aggregated_metrics: AggregatedMetricsAnalysis = Field(None, \
        description = "aggregated metrics", alias = "aggregatedMetrics")
    version_assessments: VersionAssessmentsAnalysis = Field(None, \
        description = "version assessments", alias = "versionAssessments")
    winner_assessment: WinnerAssessmentAnalysis = Field(None, \
        description = "winner assessment", alias = "winnerAssessment")
    weights: WeightsAnalysis = Field(None, description = "weight recommendations")

    def convert_to_float(self):
        """
        Apply convert_to_float on aggregatedMetric
        """
        if self.aggregated_metrics is not None:
            self.aggregated_metrics = self.aggregated_metrics.convert_to_float()
        return self

    def convert_to_quantity(self):
        """
        Apply convert_to_quantiy on aggregatedMetric
        """
        if self.aggregated_metrics is not None:
            self.aggregated_metrics = self.aggregated_metrics.convert_to_quantity()
        return self

class ExperimentStatus(BaseModel):
    """
    Pydantic model for experiment status subresource
    """
    startTime: datetime = Field(..., description = "starttime of the experiment")
    metrics: Sequence[MetricInfo] = Field(None, description = "Sequence of \
        MetricInfo objects")
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
