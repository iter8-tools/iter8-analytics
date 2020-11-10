"""
    Experiment methods
"""
# core python dependencies
import logging

# iter8 dependencies
from iter8_analytics.api.v2.types import ExperimentResource, \
    ExperimentResourceAndMetricResources, VersionAssessments, \
    WinnerAssessment, Weights, Analysis

logger = logging.getLogger('iter8_analytics')

def get_version_assessments(experiment_resource: ExperimentResource):
    """
    Get version assessments using experiment resource.
    """
    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    data = []
    warnings = []

    # available_metrics = map(lambda am: am.name, \
    #     experiment_resource.status.analysis.aggregatedMetrics.data)

    # satisfiesObjectives = {}
    # for version in versions:
    #     satisfiesObjectives[version.name] = [False] * len(experiment_resource.criteria.objectives)

    # for ind, obj in enumerate(experiment_resource.criteria.objectives):
    #     if obj.metric in available_metrics:
    #         for version in versions:
    #             # check if metric object is available for this version
    #             # if available:
    #                 # check if metric value is none
    #                 # if not none
    #                     # check limits
    #                     # update satisfiesObjectives array
    #                 # else
    #                     # does not satisfy; update satisfiesObjectives array
    #                     # warnings.append and logger.error; this version does not satisfy this objective.
    #             # else: warnings.append and logger.error; this version does not satisfy this objective.
    #     else:
    #         warnings.append(ValueError(f"Values for {obj.metric} metric is unavailable."))
    #         logger.error(f"Values for {obj.metric} metric is unavailable.")
    #     # check if metric object is available as part of aggregated metrics

    version_assessments = VersionAssessments(data = data, message = None)
    if warnings:
        version_assessments.message = "Warnings: " + \
            ', '.join(map(lambda warning: warning.message, warnings))
    else:
        version_assessments.message = "All ok"
    return version_assessments

def get_winner_assessment(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource.
    """
    winner_assessment = WinnerAssessment(dummy = 2)
    return winner_assessment

def get_weights(experiment_resource: ExperimentResource):
    """
    Get weights using experiment resource.
    """
    weights = Weights(dummy = 2)
    return weights

def get_analytics_results(ermr: ExperimentResourceAndMetricResources):
    """
    Get analytics results using experiment resource and metric resources.
    """
    analytics_results = Analysis(dummy = 2)
    return analytics_results
