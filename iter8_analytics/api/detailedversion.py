"""
Module containing classes to run an iteration of an iter8 eperiment, and return assessment and recommendations
"""
# core python dependencies
import logging
from typing import Dict

# external module dependencies
import numpy as np

# iter8 dependencies
from iter8_analytics.api.types import *
from iter8_analytics.api.metrics import *
from iter8_analytics.api.utils import *
from iter8_analytics.api.detailedmetric import *
from iter8_analytics.api.detailedcriterion import *

from iter8_analytics.constants import ITER8_REQUEST_COUNT

logger = logging.getLogger('iter8_analytics')


class DetailedVersion():
    """Base class for a version.

    Attributes:
        spec (str): version spec
        id (str): unique iter8id of this version. contained in spec.
        is_baseline (bool): boolean indicating if this is the baseline version
        experiment (Experiment): parent experiment object to which this detailed version belongs
        pseudo_reward (float): value used to evaluate version in place of reward, if there is no reward metric in the list of criteria
    """

    def __init__(self, spec, is_baseline, experiment, pseudo_reward):
        """Initialize detailed version object.

        Args:
            spec (str): version spec
            id (str): unique iter8id of this version. contained in spec.
            version_labels (dict): version labels dict from spec
            is_baseline (bool): boolean indicating if this is the baseline version
            experiment (Experiment): parent experiment object to which this detailed version belongs
        """
        self.spec = spec  # there's some duplication here. Ok for now.
        self.id = spec.id
        self.version_labels = spec.version_labels
        self.is_baseline = is_baseline
        self.experiment = experiment  # link back to parent experiment
        self.pseudo_reward = pseudo_reward

        self.metrics = {
            "counter_metrics": {
                cms.id: DetailedCounterMetric(cms, self) for cms in self.experiment.counter_metric_specs.values()
            },
            "ratio_metrics": {
                rms.id: DetailedRatioMetric(rms, self) for rms in self.experiment.ratio_metric_specs.values()
            }
        }

        self.detailed_criteria = {
            cri.id: DetailedCriterion(cri, self) for cri in self.experiment.eip.criteria
        }

        # populated aggregated counter and ratio metrics from last state
        if experiment.eip.last_state:
            if experiment.eip.last_state.aggregated_counter_metrics:
                if self.id in experiment.eip.last_state.aggregated_counter_metrics:
                    for metric_id in experiment.eip.last_state.aggregated_counter_metrics[self.id]:
                        self.metrics["counter_metrics"][metric_id].set_aggregated_metric(
                            experiment.eip.last_state.aggregated_counter_metrics[self.id][metric_id])

            if experiment.eip.last_state.aggregated_ratio_metrics:
                if self.id in experiment.eip.last_state.aggregated_ratio_metrics:
                    for metric_id in experiment.eip.last_state.aggregated_ratio_metrics[self.id]:
                        self.metrics["ratio_metrics"][metric_id].set_aggregated_metric(
                            experiment.eip.last_state.aggregated_ratio_metrics[self.id][metric_id])

        # self.threshold_breached = {
        #     criterion.id: None for criterion in self.experiment.eip.criteria if criterion.threshold
        # }
        # self.probability_of_satisfying_threshold = {
        #     criterion.id: None for criterion in self.experiment.eip.criteria if criterion.threshold
        # }

    def aggregate_counter_metrics(self, new_counter_metrics: Dict[iter8id, CounterDataPoint]):
        """combine aggregated counter metrics from last state for this version with new counter metrics. Aggregated results stored in self.aggregated_counter_metrics

        Args:
            new_counter_metrics (Dict[iter8id, CounterDataPoint]): dictionary mapping from metric id to CounterDataPoint
        """
        for metric_id in new_counter_metrics:
            logger.debug(
                f"Aggregated counter metric before. Version: {self.id} Metric: {metric_id} Aggregated Counter Metric: {self.metrics['counter_metrics'][metric_id].aggregated_metric}")

            old_val = self.metrics['counter_metrics'][metric_id].aggregated_metric.value
            new_val = new_counter_metrics[metric_id].value
            if new_val is not None:
                if old_val is not None and old_val > new_val:
                    break  # counters should only increase. new_val is zero

                self.metrics["counter_metrics"][metric_id].set_aggregated_metric(
                    AggregatedCounterDataPoint(** new_counter_metrics[metric_id].dict()))

            logger.debug(
                f"Aggregated counter metric after. Version: {self.id} Metric: {metric_id} Aggregated Counter Metric: {self.metrics['counter_metrics'][metric_id].aggregated_metric}")

    def aggregate_ratio_metrics(self, new_ratio_metrics: Dict[iter8id, RatioDataPoint]):
        """combine aggregated ratio metrics from last state for this version with new ratio metrics. Aggregated results stored in self.aggregated_ratio_metrics

        Args:
            new_ratio_metrics (Dict[iter8id, RatioDataPoint]): dictionary mapping from metric id to RatioDataPoint
        """
        for metric_id in new_ratio_metrics:
            logger.debug(
                f"Aggregated ratio metric before. Version: {self.id} Metric: {metric_id} Aggregated Ratio Metric: {self.metrics['ratio_metrics'][metric_id].aggregated_metric}")

            if new_ratio_metrics[metric_id].value is not None:
                logger.debug(
                    f"New Ratio metric. Version: {self.id} Metric: {metric_id} New Ratio Metric: {new_ratio_metrics[metric_id]}")

                # prefer all_ok to zeroed_ratio
                if new_ratio_metrics[metric_id].status == StatusEnum.zeroed_ratio:
                    if self.metrics['ratio_metrics'][metric_id].aggregated_metric.status == StatusEnum.all_ok:
                        break

                # otherwise, go ahead and update
                self.metrics["ratio_metrics"][metric_id].set_aggregated_metric(AggregatedRatioDataPoint(
                    ** new_ratio_metrics[metric_id].dict()
                ))

            logger.debug(
                f"Aggregated ratio metric after. Version: {self.id} Metric: {metric_id} Aggregated Ratio Metric: {self.metrics['ratio_metrics'][metric_id].aggregated_metric}")

    def update_beliefs(self):
        """Update beliefs for ratio metrics. If belief update is not possible due to insufficient data, then the relevant status codes are populated here
        """
        for rm in self.metrics["ratio_metrics"].values():
            logger.debug(f"Version: {self.id} Metric: {rm.metric_id}")
            logger.debug(f"detailed metric: {rm.aggregated_metric}")
            rm.update_belief()
            logger.debug(f"Updated belief: {vars(rm.belief)}")

    def create_ratio_metric_samples(self):
        """Create ratio metric samples used for assessment and traffic routing
        """
        for rm in self.metrics["ratio_metrics"].values():
            if rm.belief.status == StatusEnum.all_ok:
                rm.belief.sample_posterior()

    def get_reward_sample(self):
        self.reward_metric_id = None
        for criterion in self.experiment.eip.criteria:
            if criterion.is_reward:
                self.reward_metric_id = criterion.metric_id
                break

        if not self.reward_metric_id:  # return pseudo-reward
            return np.full((Belief.sample_size, ), np.float(self.pseudo_reward))
        else:  # try and return a real reward
            rm = self.metrics["ratio_metrics"][self.reward_metric_id]
            if rm.belief.status == StatusEnum.all_ok:
                return rm.belief.sample_posterior()
            else:
                return np.full((Belief.sample_size, ), np.nan)

    def get_criteria_mask(self):
        product_cm = np.ones((Belief.sample_size, ))
        logger.debug(f"Creating criteria mask for version: {self.id}")
        for criterion in self.experiment.eip.criteria:
            cm = self.detailed_criteria[criterion.id].get_criterion_mask()
            logger.debug(f"Criteria with metric {criterion.metric_id}")
            logger.debug(cm)
            product_cm *= cm
        return product_cm

    def create_criteria_assessments(self):
        """Create assessment for this version. Results are stored in self.criterion_assessments
        """
        for dc in self.detailed_criteria.values():
            dc.create_assessment()
        self.criterion_assessments = [self.detailed_criteria[cri.id].get_assessment(
        ) for cri in self.experiment.eip.criteria]


class DetailedBaselineVersion(DetailedVersion):
    def __init__(self, spec, experiment):
        # baseline always has pseudo_reward = 1.0
        super().__init__(spec, True, experiment, 1.0)

    # def check_threshold_breaches(self):
    #     """Check if thresholds have been breached in criteria
    #     """
    #     self.threshold_breached = {
    #         criterion.id: self.check_breach(** self.get_threshold_details(criterion, self)) for criterion in self.experiment.eip.criteria if criterion.threshold
    #     }


class DetailedCandidateVersion(DetailedVersion):
    def __init__(self, spec, experiment, pseudo_reward):
        super().__init__(spec, False, experiment, pseudo_reward)

    # def check_threshold_breaches(self):
    #     """Check if thresholds have been breached in criteria
    #     """
    #     self.threshold_breached = {
    #         criterion.id: self.check_breach(** self.get_threshold_details(criterion, self)) for criterion in self.experiment.eip.criteria if criterion.threshold
    #     }

    # def check_threshold_breaches(self):
    #     """Check if thresholds have been breached in criteria
    #     """
    #     self.threshold_breached = {
    #         criterion.id: self.check_breach(** self.get_threshold_details(criterion, self.detailed_baseline_versions)) for criterion in self.experiment.eip.criteria if criterion.threshold
    #     }
