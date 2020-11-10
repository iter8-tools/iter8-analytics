"""
Module containing pydantic data models for iter8 v2
"""
# core python dependencies
from typing import Sequence, Dict
from datetime import datetime

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

# class Criteria(BaseModel):
#     """
#     Pydantic model for Criteria
#     """
#     dummy: int

class ExperimentSpec(BaseModel):
    """
    Pydantic model for experiment spec subresource
    """
    versionInfo: VersionInfo = Field(..., description = "versions in the experiment")
    # criteria: Criteria

class ExperimentStatus(BaseModel):
    """
    Pydantic model for experiment status subresource
    """
    startTime: datetime = Field(..., description = "Start time of the experiment")

class ExperimentResource(BaseModel):
    """
    Pydantic model for experiment resource
    """
    spec: ExperimentSpec = Field(..., description = "Experiment spec subresource")
    status: ExperimentStatus = Field(..., description = "Experiment status subresource")

class ObjectMeta(BaseModel):
    """
    Pydantic model for k8s object meta
    """
    name: str = Field(..., description = "Name of the k8s resource")

class MetricSpec(BaseModel):
    """
    Pydantic model for metric spec subresource
    """
    params: Dict[str, str] = Field(None, description = "Parameters to be used \
        as part of the REST query for this metric")
    provider: str = Field(..., description = "Identifier for the metrics backend")

class MetricResource(BaseModel):
    """
    Pydantic model for metric resource
    """
    metadata: ObjectMeta = Field(..., description = "Metrics resource metadata")
    spec: MetricSpec = Field(..., description = "Metrics resource spec")

class ExperimentResourceAndMetricResources(BaseModel):
    """
    Pydantic model that encapsulates experiment resource and a list of metric resources
    """
    experimentResource: ExperimentResource = Field(..., description="Experiment resource")
    metricResources: Sequence[MetricResource] = Field(..., \
        description="a sequence of metric resources")

class VersionMetric(BaseModel):
    """
    Metrics object for a version
    """
    name: str = Field(..., description = "version name")
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
    Pydantic model for an aggregated metric
    """
    name: str = Field(..., description = "metric name")
    max: float = Field(None, description = "maximum observed value for this metric")
    min: float = Field(None, description = "minimum observed value for this metric")
    # min_items == 1 since at least one version (baseline) will be present
    versions: conlist(VersionMetric, min_items = 1) = Field(..., \
        description = "a sequence of metrics objects, one for each version")

class Iter8v2AggregatedMetrics(BaseModel):
    """
    Pydantic model for aggregated metrics response
    """
    data: Sequence[AggregatedMetric] = Field(..., \
    description = "Sequence of AggregatedMetric objects")
    message: str = Field(None, description = "Human-readable description of aggregated metrics")

class Iter8v2VersionAssessments(BaseModel):
    """
    Pydantic model for version assessments returned by iter8 analytics v2
    """
    dummy: int

class Iter8v2WinnerAssessment(BaseModel):
    """
    Pydantic model for winner assessment returned by iter8 analytics v2
    """
    dummy: int

class Iter8v2Weights(BaseModel):
    """
    Pydantic model for weights returned by iter8 analytics v2
    """
    dummy: int

class Iter8v2AnalyticsResults(BaseModel):
    """
    Pydantic model for analytics results returned by iter8 analytics v2
    """
    dummy: int
    