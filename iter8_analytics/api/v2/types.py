"""
Module containing pydantic data models for iter8 v2
"""
# core python dependencies
from typing import Sequence, Dict
from datetime import datetime
from enum import Enum

# external module dependencies
from pydantic import BaseModel, Field, conlist

class Version(BaseModel):
    """
    Pydantic model for Version
    """
    name: str = Field(..., description = "version name")
    tags: Dict[str, str] = Field(None, descriptiopn = "version tags (key-value pairs)")

class VersionInfo(BaseModel):
    """
    Pydantic model for versionInfo field in experiment spec subresource
    """
    baseline: Version = Field(..., description = "baseline version")
    candidates: Sequence[Version] = Field(None, description = "a list of candidate versions")

class Objective(BaseModel):
    """
    Pydantic model for experiment objective
    """
    metric: str = Field(..., description = "metric name")
    upperLimit: float = Field(None, description = "upper limit for the metric")
    lowerLimit: float = Field(None, description = "lower limit for the metric")

class Criteria(BaseModel):
    """
    Pydantic model for Criteria field in experiment spec
    """
    objectives: Sequence[Objective] = Field(None, description = "sequence of objectives")

class ExperimentType(str, Enum):
    """
    Experiment types
    """
    canary = "canary"
    ab = "A/B"
    performance = "performance"
    bluegreen = "BlueGreen"

class WeightAlgorithm(str, Enum):
    """
    Algorithm types
    """
    progressive = "progressive"
    fixed = "fixed-split"

class WeightsConfig(BaseModel):
    """
    Pydantic model for weights configuration in experiment spec
    """
    maxCandidateWeight: int = Field(100, description = "units = percent; \
        candidate weight never exceeds this value", le = 100, ge = 0)
    maxCandidateWeightIncrement: int = Field(5, description = "units = percent; \
        candidate weight increment never exceeds this value", le = 100, ge = 0)
    algorithm: WeightAlgorithm = Field(WeightAlgorithm.progressive, description = \
        "weight computation algorithm")

class ExperimentStrategy(BaseModel):
    """
    Experiment strategy
    """
    type: ExperimentType = Field(..., \
        description="indicates preference for metric values -- lower, higher, or None (default)")
    weights: WeightsConfig = Field(None, \
        description = "weights configuration")

class ExperimentSpec(BaseModel):
    """
    Pydantic model for experiment spec subresource
    """
    strategy: ExperimentStrategy = Field(..., \
        description = "experiment strategy")
    versionInfo: VersionInfo = Field(..., description = "versions in the experiment")
    criteria: Criteria = Field(None, description = "experiment criteria")

class ObjectMeta(BaseModel):
    """
    Pydantic model for k8s object meta
    """
    name: str = Field(..., description = "name of the k8s resource")

class MetricSpec(BaseModel):
    """
    Pydantic model for metric spec subresource
    """
    params: Dict[str, str] = Field(None, description = "parameters to be used \
        as part of the REST query for this metric")
    provider: str = Field(..., description = "identifier for the metrics backend")

class MetricResource(BaseModel):
    """
    Pydantic model for metric resource
    """
    metadata: ObjectMeta = Field(..., description = "metrics resource metadata")
    spec: MetricSpec = Field(..., description = "metrics resource spec")

class VersionMetric(BaseModel):
    """
    Pydantic model for a version metric object
    """
    max: float = Field(None, description = "maximum observed value \
        for this metric for this version")
    min: float = Field(None, description = "minimum observed value \
        for this metric for this version")
    value: float = Field(None, description = "last observed value \
        for this metric for this version")
    sample_size: float = Field(None, description = "last observed value \
        for the sample_size metric for this version; this is none if sample_size is not specified")

class AggregatedMetric(BaseModel):
    """
    Pydantic model for an aggregated metric object
    """
    max: float = Field(None, description = "maximum observed value for this metric")
    min: float = Field(None, description = "minimum observed value for this metric")
    # min_items == 1 since at least one version (baseline) will be present
    data: Dict[str, VersionMetric] = Field(..., \
        description = "dictionary with version names as keys and VersionMetric objects as values")

class AggregatedMetrics(BaseModel):
    """
    Pydantic model for aggregated metrics response
    """
    data: Dict[str, AggregatedMetric] = Field(..., \
    description = "dictionary with metric names as keys and AggregatedMetric objects as values")
    message: str = Field(None, description = "human-readable description of aggregated metrics")

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
    value: float = Field(..., description = "weight for a version", ge = 0.0)

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

class ExperimentStatus(BaseModel):
    """
    Pydantic model for experiment status subresource
    """
    startTime: datetime = Field(..., description = "starttime of the experiment")
    analysis: Analysis = Field(None, description = "currently available analysis")

class ExperimentResource(BaseModel):
    """
    Pydantic model for experiment resource
    """
    spec: ExperimentSpec = Field(..., description = "experiment spec subresource")
    status: ExperimentStatus = Field(..., description = "experiment status subresource")

class ExperimentResourceAndMetricResources(BaseModel):
    """
    Pydantic model that encapsulates experiment resource and a list of metric resources
    """
    experimentResource: ExperimentResource = Field(..., description="experiment resource")
    metricResources: Sequence[MetricResource] = Field(..., \
        description="a sequence of metric resources")
