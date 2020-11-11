"""
    Experiment methods
"""
# core python dependencies
import logging

# iter8 dependencies
from iter8_analytics.api.v2.types import ExperimentResource, \
    ExperimentResourceAndMetricResources, VersionAssessments, \
    WinnerAssessment, Weights, Analysis, Objective

logger = logging.getLogger('iter8_analytics')

def get_version_assessments(experiment_resource: ExperimentResource):
    """
    Get version assessments using experiment resource.
    """
    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    data = []
    messages = []

    def collect_messages_and_log(message: str):
        messages.append(message)
        logger.error(message)

    def check_limits(obj: Objective, value: float):
        if (obj.upperLimit is not None) and (value > obj.upperLimit):
            return False
        if (obj.lowerLimit is not None) and (value < obj.lowerLimit):
            return False
        return True

    aggregated_metric_data = experiment_resource.status.analysis.aggregatedMetrics.data

    version_assessments = VersionAssessments(data = {}, message = None)

    if experiment_resource.spec.criteria is None:
        return version_assessments

    for version in versions:
        version_assessments.data[version.name] = [False] * \
            len(experiment_resource.spec.criteria.objectives)

    for ind, obj in enumerate(experiment_resource.spec.criteria.objectives):
        if obj.metric in aggregated_metric_data:
            versions_metric_data = aggregated_metric_data[obj.metric].data
            for version in versions:
                if version.name in versions_metric_data:
                    if versions_metric_data[version.name].value is not None:
                        version_assessments.data[version.name][ind] = \
                            check_limits(obj, versions_metric_data[version.name].value)
                    else:
                        collect_messages_and_log(f"Value for \
                            {obj.metric} metric and {version.name} version is None.")
                else:
                    collect_messages_and_log(f"Value for \
                        {obj.metric} metric and {version.name} version is unavailable.")
        else:
            collect_messages_and_log(f"Aggregated metric object for {obj.metric} \
                metric is unavailable.")

    if messages:
        version_assessments.message = "Warnings: " + ', '.join(messages)
    else:
        version_assessments.message = "All ok"
    return version_assessments

def get_winner_assessment(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource.
    """
    logger.debug(experiment_resource)
    winner_assessment = WinnerAssessment()

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    # feasible_versions = filter(lambda version: \
    # all(experiment_resource.status.analysis.versionAssessments.data[version.name]), versions)
    return winner_assessment

def get_weights(experiment_resource: ExperimentResource):
    """
    Get weights using experiment resource.
    """
    logger.debug(experiment_resource)
    weights = Weights(dummy = 2)
    return weights

def get_analytics_results(ermr: ExperimentResourceAndMetricResources):
    """
    Get analytics results using experiment resource and metric resources.
    """
    analytics_results = Analysis(dummy = 2)
    return analytics_results
