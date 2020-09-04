"""
Module containing detailed criterion classes
"""
# core python dependencies
import logging
# from typing import Dict

# external module dependencies
import numpy as np

# iter8 dependencies
from iter8_analytics.api.analytics.types import *
# from iter8_analytics.api.analytics.metrics import *
# from iter8_analytics.api.analytics.utils import *
from iter8_analytics.api.analytics.detailedmetric import *
# from iter8_analytics.api.analytics.detailedcriterion import *

logger = logging.getLogger('iter8_analytics')


class DetailedCriterion():
    """Base class for a detailed criterion.

    Attributes:
        spec (CriterionSpec): criterion spec
    """

    def __init__(self, criterion_spec, detailed_version):
        """Initialize detailed criterion object.

        Args:
            criterion_spec (CriterionSpec): criterion spec
            detailed_version (DetailedVersion): detailed version to which this detailed criterion belongs   
        """
        self.spec = criterion_spec
        self.detailed_version = detailed_version
        # some redundancy is ok
        self.id = self.spec.id
        self.metric_id = self.spec.metric_id
        self.is_counter = self.metric_id in self.detailed_version.metrics["counter_metrics"]
        if self.is_counter:
            self.detailed_metric = self.detailed_version.metrics["counter_metrics"][self.metric_id]
        else:
            self.detailed_metric = self.detailed_version.metrics["ratio_metrics"][self.metric_id]

    def create_assessment(self):
        self.assessment = CriterionAssessment(
            id=self.id,
            metric_id=self.metric_id,
            statistics=self.create_statistics(),
            threshold_assessment=self.create_threshold_assessment()
        )

    def create_statistics(self):
        if self.is_counter:
            return Statistics(value=self.detailed_version.metrics["counter_metrics"][self.metric_id].aggregated_metric.value)
        else:  # criterion.metric_id is ratio
            return Statistics(value=self.detailed_version.metrics["ratio_metrics"][self.metric_id].aggregated_metric.value,
                              ratio_statistics=self.get_ratio_statistics())

    def get_ratio_statistics(self):
        rm = self.detailed_version.metrics["ratio_metrics"][self.metric_id]
        b = rm.belief
        if b.status == StatusEnum.uninitialized_belief:
            return None
        # if samples for this metric are all nans, return None
        ms = b.sample_posterior()
        if np.any(np.isnan(ms)):
            return None
        # if samples for this metric are all constant, return None
        if np.min(ms) == np.max(ms):
            return None
        # compute credible interval based on sample
        gap = (
            1.0 - AdvancedParameters.posterior_probability_for_credible_intervals)*100.0
        cilp = gap / 2.0
        ciup = (
            gap/2.0) + AdvancedParameters.posterior_probability_for_credible_intervals*100.0
        ci = Interval(
            lower=max(0.0, np.percentile(ms, cilp)),
            upper=max(0.0, np.percentile(ms, ciup)))  # don't allow negative values
        # else, get samples of this metric for baseline, and all other candidates
        # compute the relevant statistics and return ratio metrics
        # tbd
        return RatioStatistics(credible_interval=ci)

    def get_criterion_mask(self):
        ms = self.detailed_metric.metric_spec
        if not self.spec.threshold:
            logger.debug(
                f"No threshold for {ms.id} for {self.detailed_version.id}")
            logger.debug("Returning ones")
            return np.ones((Belief.sample_size, )).astype(np.float)
        else:
            if self.threshold_assessment is None:
                return np.zeros((Belief.sample_size, )).astype(np.float)
            p = self.threshold_assessment.probability_of_satisfying_threshold
            if p is None:
                return np.zeros((Belief.sample_size, )).astype(np.float)
            return np.random.binomial(1, p, (Belief.sample_size, )).astype(np.float)

            # if self.is_counter: # counter metric. lower is preferred.
            #     if ms.preferred_direction == DirectionEnum.lower:
            #         if self.detailed_metric.aggregated_metric.value <= self.spec.threshold.value:
            #             logger.debug(f"Counter metric {ms.id} within threshold for {self.detailed_version.id}")
            #             logger.debug("Returning ones")
            #             return np.ones((Belief.sample_size, )).astype(np.float)
            #         else:
            #             logger.debug(f"Counter metric {ms.id} violating threshold for {self.detailed_version.id}")
            #             logger.debug("Returning zeros")
            #             return np.zeros((Belief.sample_size, )).astype(np.float)
            #     else: # ms.preferred_direction == DirectionEnum.higher:
            #         if self.detailed_metric.aggregated_metric.value >= self.spec.threshold.value:
            #             logger.debug(f"Counter metric {ms.id} within threshold for {self.detailed_version.id}")
            #             logger.debug("Returning ones")
            #             return np.ones((Belief.sample_size, )).astype(np.float)
            #         else:
            #             logger.debug(f"Counter metric {ms.id} violating threshold for {self.detailed_version.id}")
            #             logger.debug("Returning zeros")
            #             return np.zeros((Belief.sample_size, )).astype(np.float)
            # else: # self.is_counter == False. Ratio metric.
            #     rm = self.detailed_version.metrics["ratio_metrics"][self.metric_id]
            #     b = rm.belief
            #     if b.status == StatusEnum.uninitialized_belief:
            #         logger.debug(f"Uninitialized belief for metric {ms.id} for {self.detailed_version.id}")
            #         logger.debug("Returning zeros")
            #         return np.zeros((Belief.sample_size, )).astype(np.float) # nothing is known about this version
            #     # if samples for this metric are all nans, return None
            #     sample = b.sample_posterior()
            #     if np.any(np.isnan(sample)):
            #         logger.debug(f"Nan values in  metric sample {ms.id} for {self.detailed_version.id}")
            #         logger.debug("Returning zeros")
            #         return np.zeros((Belief.sample_size, )).astype(np.float) # can't use nan values
            #     else:
            #         logger.debug(f"Returning posterior indicators for metric {ms.id} for {self.detailed_version.id}")
            #         if self.spec.threshold.threshold_type == ThresholdEnum.absolute:
            #             if ms.preferred_direction == DirectionEnum.lower:
            #                 return (sample <= self.spec.threshold.value).astype(np.float)
            #             else:
            #                 return (sample >= self.spec.threshold.value).astype(np.float)
            #         else: # relative threshold
            #             baseline = self.detailed_version.experiment.detailed_baseline_version
            #             if self.detailed_version.id == baseline.id:
            #                 # baseline is always assumed to satisfy relative thresholds
            #                 logger.debug(f"Relative thresholds for metric {ms.id} for baseline version {self.detailed_version.id}")
            #                 logger.debug("Returning ones as criteria mask")
            #                 return np.ones((Belief.sample_size, )).astype(np.float)

            #             baseline_belief = baseline.metrics["ratio_metrics"][self.metric_id].belief
            #             if baseline_belief.status == StatusEnum.uninitialized_belief:
            #                 logger.debug(f"Uninitialized baseline belief for metric {ms.id} for {self.detailed_version.id}")
            #                 logger.debug("Returning zeros as criteria mask")
            #                 return np.zeros((Belief.sample_size, )).astype(np.float) # nothing is known about this version

            #             baseline_sample = baseline_belief.sample_posterior() # go to the baseline and get its sample for this ratio metric
            #             if ms.preferred_direction == DirectionEnum.lower:
            #                 logger.debug(f"Computing criteria mask with relative threshold: {self.detailed_version.id}")
            #                 logger.debug(f"sample: {sample}")
            #                 logger.debug(f"sample: {baseline_sample}")
            #                 logger.debug(f"{(sample <= baseline_sample * self.spec.threshold.value).astype(np.float)}")
            #                 return (sample <= baseline_sample * self.spec.threshold.value).astype(np.float)
            #             else:
            #                 return (sample >= baseline_sample * self.spec.threshold.value).astype(np.float)

    def get_assessment(self):
        return self.assessment

    def create_threshold_assessment(self):
        """Create threshold assessment.

        Args:
            criterion (Criterion): A criterion object from the experiment with a threshold

        Returns:
            threshold (ThresholdAssessment): A threshold assessment object or none if metric values are unavailable to create the assessment
        """
        # local function to help in assessment
        def check_breach(data_point, limit, preferred_direction):
            """Check if metric value has breached a limit.

                Args:
                    data_point (DataPoint): aggregated counter or ratio data point
                    limit (float): limit to be checked
                    preferred_direction (DirectionEnum): preferred direction for the metric

                Returns:
                    status (bool): True if the data point has breached threshold. False otherwise.
            """
            assert(data_point.value is not None)
            assert(limit is not None)

            if preferred_direction == DirectionEnum.lower:
                return data_point.value > limit
            elif preferred_direction == DirectionEnum.higher:
                return data_point.value < limit

        def compute_probability_of_satisfying_threshold(lhs_sample, rhs, preferred_direction):
            assert(lhs_sample is not None)
            assert(rhs is not None)
            assert(not np.any(np.isnan(lhs_sample)))
            assert(not np.any(np.isnan(rhs)))

            if ms.preferred_direction == DirectionEnum.lower:
                return np.sum((lhs_sample <= rhs).astype(np.float))/np.size(lhs_sample)
            else:
                return np.sum((lhs_sample >= rhs).astype(np.float))/np.size(lhs_sample)

        def bad_belief(belief):
            if belief.status == StatusEnum.uninitialized_belief:
                return True
            sample = belief.sample_posterior()
            if np.any(np.isnan(sample)):
                return True
            return False

        ms = self.detailed_metric.metric_spec
        if not self.spec.threshold:
            logger.debug(
                f"No threshold for {ms.id} for {self.detailed_version.id}")
            self.threshold_assessment = None
            return None
        else:  # there is a threshold specified
            if self.detailed_metric.aggregated_metric.value is None:
                self.threshold_assessment = None  # nothing to check
                return None

            if self.spec.threshold.threshold_type == ThresholdEnum.absolute:
                # well defined value for this metric
                breach = check_breach(self.detailed_metric.aggregated_metric,
                                      self.spec.threshold.value, ms.preferred_direction)
                # got breach. As soon as we get post, we can return...
                if self.is_counter:
                    self.threshold_assessment = ThresholdAssessment(
                        threshold_breached=breach,
                        probability_of_satisfying_threshold=1.0 - float(breach)
                    )
                    return self.threshold_assessment
                else:  # ratio metric. got breach. trying to get post
                    b = self.detailed_metric.belief
                    if bad_belief(b):
                        logger.debug(
                            f"Uninitialized belief of belief with nans for metric {ms.id} for {self.detailed_version.id}")
                        self.threshold_assessment = ThresholdAssessment(
                            threshold_breached=breach,
                            probability_of_satisfying_threshold=None
                        )
                        return self.threshold_assessment
                    else:  # posterior sampling is possible. Good sample
                        # if samples for this metric are all nans, return None
                        logger.debug(
                            f"Returning posterior indicators for metric {ms.id} for {self.detailed_version.id}")
                        self.threshold_assessment = ThresholdAssessment(
                            threshold_breached=breach,
                            probability_of_satisfying_threshold=compute_probability_of_satisfying_threshold(
                                b.sample_posterior(), self.spec.threshold.value, ms.preferred_direction)
                        )
                        return self.threshold_assessment

            else:  # relative threshold. Defined only for ratio metrics.
                baseline = self.detailed_version.experiment.detailed_baseline_version
                if self.detailed_version.id == baseline.id:  # this is the baseline
                    self.threshold_assessment = None
                    return None
                else:  # this is a candidate version
                    # baseline detailed metric
                    bdm = baseline.metrics["ratio_metrics"][self.metric_id]
                    if bdm.aggregated_metric.value is None:  # nothing to compare against
                        self.threshold_assessment = None
                        return None
                    else:  # well defined baseline value
                        breach = check_breach(self.detailed_metric.aggregated_metric,
                                              bdm.aggregated_metric.value * self.spec.threshold.value, ms.preferred_direction)

                        b = self.detailed_metric.belief
                        if bad_belief(b) or bad_belief(bdm.belief):
                            self.threshold_assessment = ThresholdAssessment(
                                threshold_breached=breach,
                                probability_of_satisfying_threshold=None
                            )
                            return self.threshold_assessment
                        else:  # baseline sample also looks good
                            logger.debug(
                                f"Comparing candidate {self.detailed_version.id} with baseline {baseline.id} for metric {self.metric_id} with relative threshold of {self.spec.threshold.value}")
                            logger.debug(
                                f"Candidate's posterior: {b.sample_posterior()}")
                            logger.debug(
                                f"Baseline's posterior: {bdm.belief.sample_posterior()}")
                            post = compute_probability_of_satisfying_threshold(b.sample_posterior(
                            ), bdm.belief.sample_posterior() * self.spec.threshold.value, ms.preferred_direction)
                            logger.debug(f"post looks good: {post}")
                            self.threshold_assessment = ThresholdAssessment(
                                threshold_breached=breach,
                                probability_of_satisfying_threshold=post
                            )
                            return self.threshold_assessment
