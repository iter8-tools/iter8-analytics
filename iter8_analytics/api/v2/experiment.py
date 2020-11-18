"""
    Experiment methods
"""
# core python dependencies
import logging
import math

# external dependencies
import numpy as np

# iter8 dependencies
from iter8_analytics.api.v2.types import ExperimentResource, \
    VersionAssessments, VersionWeight, \
    WinnerAssessment, WinnerAssessmentData, Weights, Analysis, Objective, ExperimentType, \
    Reward, PreferredDirection
from iter8_analytics.api.v2.metrics import get_aggregated_metrics
from iter8_analytics.api.utils import gen_round
from iter8_analytics.api.utils import Message, MessageLevel

logger = logging.getLogger('iter8_analytics')

def get_version_assessments(experiment_resource: ExperimentResource):
    """
    Get version assessments using experiment resource.
    """
    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    messages = []

    def check_limits(obj: Objective, value: float):
        if (obj.upperLimit is not None) and (value > obj.upperLimit):
            return False
        if (obj.lowerLimit is not None) and (value < obj.lowerLimit):
            return False
        return True

    aggregated_metric_data = experiment_resource.status.analysis.aggregatedMetrics.data

    version_assessments = VersionAssessments(data = {})

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
                        messages.append(Message(MessageLevel.warning, \
                            f"Value for {obj.metric} metric and {version.name} version is None."))
                else:
                    messages.append(Message(MessageLevel.warning, \
                        f"Value for {obj.metric} metric and {version.name} version is unavailable."))
        else:
            messages.append(Message(MessageLevel.warning, \
                f"Aggregated metric object for {obj.metric} metric is unavailable."))

    version_assessments.message = Message.join_messages(messages)
    return version_assessments

def get_winner_assessment_for_canarybg(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource for Canary or BlueGreen experiments
    """
    was = WinnerAssessment()

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    feasible_versions = list(filter(lambda version: \
    all(experiment_resource.status.analysis.versionAssessments.data[version.name]), versions))

    # names of feasible versions
    fvn = list(map(lambda version: version.name, feasible_versions))

    if versions[1].name in fvn:
        was.data = WinnerAssessmentData(winnerFound = True, winner = versions[1].name)
        was.message = Message.join_messages([Message(MessageLevel.info, \
            "candidate satisfies all objectives")])
    elif versions[0].name in fvn:
        was.data = WinnerAssessmentData(winnerFound = True, winner = versions[0].name)
        was.message = Message.join_messages([Message(MessageLevel.info, \
            "baseline satisfies all objectives; candidate does not")])
    return was

def get_winner_assessment_for_abn(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource for ab or abn experiments
    """
    was = WinnerAssessment()

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    feasible_versions = list(filter(lambda version: \
    all(experiment_resource.status.analysis.versionAssessments.data[version.name]), versions))

    # names of feasible versions
    fvn = list(map(lambda version: version.name, feasible_versions))

    def get_inf_reward(reward: Reward):
        if reward.preferredDirection == PreferredDirection.high:
            return -math.inf
        else:
            return math.inf

    def first_better_than_second(first: float, second: float, \
        preferred_direction: PreferredDirection):
        """
        Return True if first is better than second, else return False
        """
        if preferred_direction is None:
            err = "Metrics cannot be compared without preferred direction"
            logger.error(err)
            return False, err
        if preferred_direction is PreferredDirection.high:
            return (first > second), None
        return (first < second), None


    aggregated_metric_data = experiment_resource.status.analysis.aggregatedMetrics.data
    if experiment_resource.spec.criteria.reward is not None:
        reward_metric = experiment_resource.spec.criteria.reward.metric
        if reward_metric in aggregated_metric_data:
            reward_metric_data = aggregated_metric_data[reward_metric].data

            (top_reward, best_versions) = (get_inf_reward(\
                experiment_resource.spec.criteria.reward.preferredDirection), [])

            messages = []

            if not fvn:
                messages.append(Message(MessageLevel.info, "no version satisfies all objectives"))

            for fver in fvn: # for each feasible version
                if fver in reward_metric_data:
                    if reward_metric_data[fver].value is not None:
                        if reward_metric_data[fver].value == top_reward:
                            best_versions.append(fver)
                        else: # this reward not equal to top reward
                            is_better, err = first_better_than_second(\
                                reward_metric_data[fver].value, top_reward, \
                                experiment_resource.spec.criteria.reward.preferredDirection)
                            if err is None:
                                if is_better:
                                    (top_reward, best_versions) = \
                                        (reward_metric_data[fver].value, [fver])
                            else: # there is an error in comparison
                                was.message = Message.join_messages(Message(MessageLevel.error, \
                                    str(err)))
                                return was
                    else: # found a feasible version without reward value
                        messages.append(Message(MessageLevel.warning, \
                            f"reward value for feasible version {fver} is not available"))
                else: # found a feasible version without reward value
                    message = f"reward value for feasible version {fver} is not available"
                    logger.warning(message)
                    messages.append(message)

            was.data.bestVersions = best_versions

            if len(best_versions) == 1:
                was.data.winnerFound = True
                was.data.winner = best_versions[0]
                messages.append(Message(MessageLevel.info, "found unique winner"))
            elif len(best_versions) > 1:
                messages.append(Message(MessageLevel.info, \
                    "no unique winner; two or more feasible versions with same reward value"))

            was.message = Message.join_messages(messages)

        else: # reward metric values are not available
            was.message = Message.join_messages(Message(MessageLevel.warning, \
                "reward metric values are not available"))

    else: # ab or abn experiment without reward metric
        was.message = Message.join_messages(Message(MessageLevel.warning, \
            "No reward metric in experiment. Winner assessment cannot be computed for ab or abn experiments without reward metric."))

    return was

def get_winner_assessment(experiment_resource: ExperimentResource):
    """
    Get winner assessment using experiment resource.
    """

    if experiment_resource.spec.strategy.type == ExperimentType.performance:
        was = WinnerAssessment()
        was.message = Message.join_messages([Message(MessageLevel.error, \
            "performance tests cannot have winner assessments")])
        return was

    elif (experiment_resource.spec.strategy.type == ExperimentType.canary) or \
        (experiment_resource.spec.strategy.type == ExperimentType.bluegreen):
        return get_winner_assessment_for_canarybg(experiment_resource)

    else:
        return get_winner_assessment_for_abn(experiment_resource)
    

def get_weights(experiment_resource: ExperimentResource):
    """
    Get weights using experiment resource.
    """
    if experiment_resource.spec.strategy.type == ExperimentType.performance:
        return Weights(data = [], \
            message = "weight computation is not applicable to a performance experiment")

    versions = [experiment_resource.spec.versionInfo.baseline]
    versions += experiment_resource.spec.versionInfo.candidates

    # note: all weight fields in yamls need to be integers

    # create exploration weights; in fraction
    exploration_weights = np.full((len(versions), ), 1.0 / len(versions))
    # create exploitation weights; in fraction
    # create mix-weight: in fraction
    mix_weights = exploration_weights
    # create mix-weight: in percent
    mix_weights *= 100.0
    # apply weight constraints; max candidate and max iteration constraints
    # perform rounding of weights, so that they sum up to 100
    integral_weights = gen_round(mix_weights, 100)
    data = []
    for version in versions:
        data.append(VersionWeight(name = version.name, value = next(integral_weights)))
    _weights = Weights(data = data)
    _weights.message = Message.join_messages([Message(MessageLevel.info, "all ok")])
    return _weights

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
