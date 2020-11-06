"""
    Experiment methods
"""
from iter8_analytics.api.v2.types import ExperimentResource, \
    ExperimentResourceAndMetricResources, Iter8v2VersionAssessments, \
    Iter8v2WinnerAssessment, Iter8v2Weights, Iter8v2AnalyticsResults

def get_version_assessments(experiment_resource: ExperimentResource):
    """
    Get version assessments using experiment resource.
    """
    version_assessments = Iter8v2VersionAssessments(dummy = 2)
    return version_assessments

def get_winner_assessment(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource.
    """
    winner_assessment = Iter8v2WinnerAssessment(dummy = 2)
    return winner_assessment

def get_weights(experiment_resource: ExperimentResource):
    """
    Get weights using experiment resource.
    """
    weights = Iter8v2Weights(dummy = 2)
    return weights

def get_analytics_results(ermr: ExperimentResourceAndMetricResources):
    """
    Get analytics results using experiment resource and metric resources.
    """
    analytics_results = Iter8v2AnalyticsResults(dummy = 2)
    return analytics_results
