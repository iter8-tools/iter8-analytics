"""
    Experiment methods
"""
# core python dependencies
import logging

# iter8 dependencies
from iter8_analytics.api.v2.types import ExperimentResource, \
    VersionAssessments, VersionWeight, \
    WinnerAssessment, WinnerAssessmentData, Weights, Analysis, Objective, ExperimentType
from iter8_analytics.api.v2.metrics import get_aggregated_metrics

logger = logging.getLogger('iter8_analytics')

def get_version_assessments(experiment_resource: ExperimentResource):
    """
    Get version assessments using experiment resource.
    """
    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

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
        version_assessments.message = "warnings: " + ', '.join(messages)
    else:
        version_assessments.message = "computed version assessments"
    return version_assessments

def get_winner_assessment(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource.
    """
    if experiment_resource.spec.strategy.type == ExperimentType.performance:
        was = WinnerAssessment()
        was.message = "performance tests have no winner assessments"
        return was

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    feasible_versions = list(filter(lambda version: \
    all(experiment_resource.status.analysis.versionAssessments.data[version.name]), versions))

    # names of feasible versions
    fvn = list(map(lambda version: version.name, feasible_versions))

    if (experiment_resource.spec.strategy.type == ExperimentType.canary) or \
        (experiment_resource.spec.strategy.type == ExperimentType.bluegreen):
        was = WinnerAssessment()
        was.message = "no version satisfies all objectives"
        if versions[1].name in fvn:
            was.data = WinnerAssessmentData(winnerFound = True, winner = versions[1].name)
            was.message = "candidate satisfies all objectives"
        elif versions[0].name in fvn:
            was.data = WinnerAssessmentData(winnerFound = True, winner = versions[0].name)
            was.message = "baseline satisfies all objectives; candidate does not"
        return was

    if experiment_resource.spec.strategy.type == ExperimentType.ab:
        pass
        # check rewards and return winner
    return WinnerAssessment()

def get_weights(experiment_resource: ExperimentResource):
    """
    Get weights using experiment resource.
    """
    if experiment_resource.spec.strategy.type == ExperimentType.performance:
        return Weights(data = [], \
            message = "weight computation is not applicable to a performance experiment")

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    # stubbing with dummy values for now
    return Weights(data = [VersionWeight(name = versions[0].name, value = 25), \
        VersionWeight(name = versions[1].name, value = 75)], message = "dummy values")

def get_analytics_results(er: ExperimentResource):
    """
    Get analysis results using experiment resource and metric resources.
    """
    exp_res = er
    exp_res.status.analysis = Analysis()
    exp_res.status.analysis.aggregatedMetrics = get_aggregated_metrics(er)
    exp_res.status.analysis.versionAssessments = get_version_assessments(exp_res)
    exp_res.status.analysis.winnerAssessment = get_winner_assessment(exp_res)
    exp_res.status.analysis.weights = get_weights(exp_res)
    return exp_res.status.analysis
