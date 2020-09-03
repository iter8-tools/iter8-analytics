"""
    Module containing classes to run an iteration of an iter8 eperiment,
    and return assessment and recommendations
"""
# core python dependencies
import logging
from datetime import datetime

# external module dependencies
import numpy as np
import pandas as pd
from fastapi import HTTPException

import iter8_analytics.api.analytics.detailedversion
from iter8_analytics.api.analytics.metrics import get_counter_metrics, \
    get_ratio_metrics, new_ratio_max_min
from iter8_analytics.api.analytics.types import ThresholdEnum, \
    ExperimentIterationParameters, DirectionEnum, TrafficSplitStrategy, VersionAssessment, \
    CandidateVersionAssessment, WinnerAssessment, AdvancedParameters, \
    Iter8AssessmentAndRecommendation
from iter8_analytics.api.analytics.utils import gen_round
from iter8_analytics.constants import ITER8_REQUEST_COUNT

# type aliases
DetailedVersion = iter8_analytics.api.analytics.detailedversion.DetailedVersion
DetailedBaselineVersion = iter8_analytics.api.analytics.detailedversion.DetailedBaselineVersion
DetailedCandidateVersion = iter8_analytics.api.analytics.detailedversion.DetailedCandidateVersion

logger = logging.getLogger('iter8_analytics')


class Experiment():
    """The experiment class which provides necessary methods
    for running a single iteration of an iter8 experiment
    """

    def __init__(self, eip: ExperimentIterationParameters):
        """Initialize the experiment object.

        Args:
            eip (ExperimentIterationParameters): Experiment iteration parameters

        Raises:
            HTTPException: Ratio metrics contain metric ids other than
            counter metric ids in their numerator or denominator.
            Unknown metric id is found in criteria. Metric marked as reward is not a ratio metric.
            There is at most one reward metric.
        """

        self.eip = eip

        # Initialized traffic split dictionary
        self.traffic_split = {}

        # Get all counter and ratio metric specs into their respective
        # dictionaries
        all_counter_metric_specs = {}
        all_ratio_metric_specs = {}
        cms, rms = None, None
        for cms in self.eip.metric_specs.counter_metrics:
            all_counter_metric_specs[cms.id] = cms
        for rms in self.eip.metric_specs.ratio_metrics:
            all_ratio_metric_specs[rms.id] = rms

        # ITER8_REQUEST_COUNT is a special metric. Lets add this always in
        # counter metrics
        self.counter_metric_specs = {}
        if ITER8_REQUEST_COUNT in all_counter_metric_specs:
            self.counter_metric_specs[ITER8_REQUEST_COUNT] = \
                all_counter_metric_specs[ITER8_REQUEST_COUNT]
        else:
            logger.error(
                "iter8_request_count metric is missing in metric specs")
            raise HTTPException(
                status_code=422,
                detail=f"{ITER8_REQUEST_COUNT} is a mandatory counter metric \
                    which is missing from the list of metric specs")
        self.ratio_metric_specs = {}

        # Initialize counter and ratio metric specs relevant to this experiment
        for cri in self.eip.criteria:
            if cri.metric_id in all_counter_metric_specs:
                # this is a counter metric
                self.counter_metric_specs[cri.metric_id] = all_counter_metric_specs[cri.metric_id]
                if cri.is_reward:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Counter metric {cri.metric_id} used as reward. \
                            Only ratio metrics can be used as a reward.")
                if cri.threshold and cri.threshold.threshold_type == ThresholdEnum.relative:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Counter metric {cri.metric_id} used with relative thresholds. \
                            Only absolute thresholds are allowed for counter metrics \
                            within criteria.")
            elif cri.metric_id in all_ratio_metric_specs:
                # this is a ratio metric
                self.ratio_metric_specs[cri.metric_id] = all_ratio_metric_specs[cri.metric_id]
                num = self.ratio_metric_specs[cri.metric_id].numerator
                den = self.ratio_metric_specs[cri.metric_id].denominator
                try:
                    self.counter_metric_specs[num] = all_counter_metric_specs[num]
                    self.counter_metric_specs[den] = all_counter_metric_specs[den]
                except KeyError as _ke:  # unknown numerator or denominator
                    logger.error(
                        "Unknown numerator or denominator found: %s", _ke)
                    raise HTTPException(
                        status_code=422,
                        detail="Unknown numerator or denominator found") from _ke
            else:  # this is an unknown metric id
                logger.error(
                    "Unknown metric id found in criteria: %s", cri.metric_id)
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown metric id found in criteria: {cri.metric_id}")

        # raise exceptions if you find more than one reward metric
        if sum(
            1 for _ in filter(
                lambda c: c.is_reward,
                self.eip.criteria)) > 1:
            # there is more than one reward metric
            raise HTTPException(
                status_code=422, detail="More than one reward criteria found")

        # raise exception if you find a criterion with a threshold and no
        # corresponding preferred_direction
        for cri in self.eip.criteria:
            if cri.threshold:
                if cri.metric_id in all_counter_metric_specs:
                    metric_spec = all_counter_metric_specs[cri.metric_id]
                else:
                    metric_spec = all_ratio_metric_specs[cri.metric_id]
                if metric_spec.preferred_direction is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Criterion uses {cri.metric_id} with a threshold, \
                            but the metric does not have a preferred direction set.")

        # Initialize detailed versions. Pseudo reward for baseline = 1.0; pseudo reward for
        # candidate is 2.0 + its index in the candidates list (i.e., the first candidate has
        # pseudo reward 2.0, 2nd has 3.0, and so on)
        self.detailed_candidate_versions = {
            spec.id: DetailedCandidateVersion(
                spec,
                self,
                index + 2) for index,
            spec in enumerate(
                self.eip.candidates)}
        self.detailed_versions = {
            ver: self.detailed_candidate_versions[ver] for ver in self.detailed_candidate_versions}
        self.detailed_baseline_version = DetailedBaselineVersion(
            self.eip.baseline, self)
        self.detailed_versions[self.eip.baseline.id] = self.detailed_baseline_version

        # check if there is a reward metric, and what its preferred direction
        # is
        self.reward_metric_id = None
        self.preferred_reward_direction = DirectionEnum.higher
        for criterion in self.eip.criteria:
            if criterion.is_reward:
                self.reward_metric_id = criterion.metric_id
                if self.ratio_metric_specs[self.reward_metric_id].preferred_direction == \
                        DirectionEnum.lower:
                    self.preferred_reward_direction = DirectionEnum.lower
                break

        # Define attributes that will be populated in various other methods
        self.new_counter_metrics = None
        self.aggregated_counter_metrics = None
        self.new_ratio_metrics = None
        self.ratio_max_mins = None
        # empty data frame to hold reward samples and criteria_masks
        self.rewards = pd.DataFrame()
        self.criteria_mask = pd.DataFrame()
        self.effective_rewards = self.rewards
        self.utilities = pd.DataFrame()
        self.win_probababilities = None
        self.traffic_split_recommendation = None

    def populate_metric_values(self):
        """
        Populate metric values in detailed versions.
        Also populate aggregated_counter_metrics and ratio_max_mins attributes.
        """
        self.new_counter_metrics = get_counter_metrics(
            self.counter_metric_specs,
            [version.spec for version in self.detailed_versions.values()],
            self.eip.start_time
        )

        for detailed_version in self.detailed_versions.values():
            detailed_version.aggregate_counter_metrics(
                self.new_counter_metrics[detailed_version.id])

        self.aggregated_counter_metrics = self.get_aggregated_counter_metrics()

        self.new_ratio_metrics = get_ratio_metrics(
            self.ratio_metric_specs,
            self.counter_metric_specs,
            self.aggregated_counter_metrics,
            [version.spec for version in self.detailed_versions.values()],
            self.eip.start_time
        )

        self.ratio_max_mins = self.get_ratio_max_mins()

        for detailed_version in self.detailed_versions.values():
            detailed_version.aggregate_ratio_metrics(
                self.new_ratio_metrics[detailed_version.id]
            )

    def run(self) -> Iter8AssessmentAndRecommendation:
        """Perform a single iteration of the experiment and return assessment and recommendation

        Returns:
            it8ar (Iter8AssessmentAndRecommendation): Iter8 assessment and recommendation
        """

        self.populate_metric_values()

        for detailed_version in self.detailed_versions.values():
            # baseline beliefs and all other version are needed for posterior
            # samples
            logger.debug("Updating beliefs for %s", detailed_version.id)
            detailed_version.update_beliefs()

        for detailed_version in self.detailed_versions.values():
            # posterior samples for ratio metrics are needed to create reward
            # and criterion masks
            detailed_version.create_ratio_metric_samples()
            # this step involves creating detailed criteria, along with reward
            # and criterion masks
            detailed_version.create_criteria_assessments()
            # reward and criteria masks are used to compute utility samples
            self.rewards[detailed_version.id] = detailed_version.get_reward_sample()
            self.criteria_mask[detailed_version.id] = detailed_version.get_criteria_mask(
            )
        # utility samples are needed for winner assessment and traffic
        # recommendations
        logger.debug("Reward sample")
        logger.debug(self.rewards.head())

        logger.debug("Criteria mask")
        logger.debug(self.criteria_mask.head())

        self.create_utility_samples()

        logger.debug("Utility sample")
        logger.debug(self.utilities.head())

        self.create_winner_assessments()
        # self.add_baseline_bias()
        self.create_traffic_recommendations()
        return self.assemble_assessment_and_recommendations()

    def create_utility_samples(self):
        """Populate the utilities attribute by combining rewards with criteria mask"""

        if self.preferred_reward_direction == DirectionEnum.higher:
            self.effective_rewards = self.rewards
        else:
            max_rewards = self.rewards.max(axis=1, skipna=False)
            self.effective_rewards = pd.DataFrame()
            for col in self.rewards.columns:
                self.effective_rewards[col] = max_rewards - self.rewards[col]

        self.effective_rewards = self.effective_rewards.fillna(0)

        logger.debug("Effective rewards")
        logger.debug(self.effective_rewards.head())

        logger.debug("Criteria mask")
        logger.debug(self.criteria_mask.head())

        # multiple effective rewards with criteria masks
        self.utilities = self.effective_rewards * self.criteria_mask
        logger.debug("Created utility samples")
        logger.debug(self.utilities.head())

    def add_baseline_bias(self):
        """Add a bias to the baseline utility to ensure
        baseline is picked when all utilities are zero.
        """
        self.utilities[self.detailed_baseline_version.id] += 1.0e-10
        logger.debug("Added baseline bias")
        logger.debug(self.utilities.head())

    def get_aggregated_counter_metrics(self):
        """Get aggregated counter metrics for this detailed version

        Returns:
            a dictionary (Dict[iter8id, AggregatedCounterMetric]):
            dictionary mapping metric id to an aggregated counter metric for this version
        """
        return {
            version.id: {
                dcm.metric_id: dcm.aggregated_metric for
                dcm in version.metrics["counter_metrics"].values()
            } for version in self.detailed_versions.values()
        }

    def get_aggregated_ratio_metrics(self):
        """Get aggregated ratio metrics for this detailed version

        Returns:
            a dictionary (Dict[iter8id, AggregatedRatioMetric]): \
            dictionary mapping metric id to an aggregated ratio metric for this version
        """
        return {
            version.id: {
                drm.metric_id: drm.aggregated_metric for
                drm in version.metrics["ratio_metrics"].values()
            } for version in self.detailed_versions.values()
        }

    def get_ratio_max_mins(self):
        """Get ratio max mins

        Returns:
            a dictionary (Dict[iter8id, RatioMaxMin]):
            dictionary mapping metric ids to RatioMaxMin for this version
        """
        metric_id_to_list_of_values = {
            metric_id: [] for metric_id in self.ratio_metric_specs
        }

        if self.eip.last_state and self.eip.last_state.ratio_max_mins:
            for metric_id in self.ratio_metric_specs:
                minimum = self.eip.last_state.ratio_max_mins[metric_id].minimum
                maximum = self.eip.last_state.ratio_max_mins[metric_id].maximum
                if minimum is not None:
                    metric_id_to_list_of_values[metric_id].append(minimum)
                    metric_id_to_list_of_values[metric_id].append(maximum)

        for version_id in self.new_ratio_metrics:
            for metric_id in self.new_ratio_metrics[version_id]:
                value = self.new_ratio_metrics[version_id][metric_id].value
                if value is not None:
                    metric_id_to_list_of_values[metric_id].append(value)
        # So far, we populated the max and min of each metric from last state,
        # along with all the metric values seen for this metric in this
        # iteration. New max min values for each metric will be derived from
        # these.
        return new_ratio_max_min(metric_id_to_list_of_values)

    def create_winner_assessments(self):
        """Create winner assessment. If winner cannot be created
        due to insufficient data, then the relevant status codes are populated.
        """
        # get the fraction of the time a particular version emerged as the
        # winner
        rank_df = self.utilities.rank(axis=1, method='min', ascending=False)
        low_rank = rank_df <= 1
        self.win_probababilities = low_rank.sum() / low_rank.sum().sum()

    def create_traffic_recommendations(self):
        """Create traffic recommendations for individual algorithms.
        """
        self.traffic_split_recommendation = {
            x: {} for x in [
                TrafficSplitStrategy.progressive,
                TrafficSplitStrategy.top_2,
                TrafficSplitStrategy.uniform]}

        for i in [1, 2, len(self.detailed_versions)]:
            self.create_top_k_recommendation(i)

        self.traffic_split_recommendation = {
            TrafficSplitStrategy.progressive: self.traffic_split[1],
            TrafficSplitStrategy.top_2: self.traffic_split[2],
            TrafficSplitStrategy.uniform: self.traffic_split[len(
                self.detailed_versions)]
        }

        self.apply_max_increment()

    def create_top_k_recommendation(self, k):
        """
        Create traffic split using the top-k PBR algorithm
        """
        self.traffic_split[k] = {}

        logger.debug("Top k split with k = %s", k)

        logger.debug("Utilities")
        logger.debug(self.utilities.head())

        # get the fractional split
        rank_df = self.utilities.rank(axis=1, method='min', ascending=False)

        logger.debug("Rank")
        logger.debug(rank_df.head())

        low_rank = rank_df <= k

        logger.debug("Low rank")
        logger.debug(low_rank.head())

        fractional_split = low_rank.sum() / low_rank.sum().sum()

        logger.debug("Fractional split: %s", fractional_split)

        uniform_split = np.full(fractional_split.shape,
                                1.0 / len(self.detailed_versions))

        logger.debug("Uniform split: %s", uniform_split)

        # exploration traffic fraction
        etf = AdvancedParameters.exploration_traffic_percentage / 100.0
        mix_split = (uniform_split * etf) + (fractional_split * (1 - etf))

        logger.debug("Mix split: %s", mix_split)

        # round the mix split so that it sums up to 100
        integral_split_gen = gen_round(mix_split * 100, 100)
        for key in self.utilities:
            self.traffic_split[k][key] = next(integral_split_gen)

    def apply_max_increment(self):
        """Create the final traffic recommendations
        """
        # apply max_increment based traffic capping

        # find the old split or initialize it to 100% baseline for all algos
        if self.eip.last_state and self.eip.last_state.traffic_split_recommendation:
            old_split = self.eip.last_state.traffic_split_recommendation
        else:
            old_split = {x: {y: 0 for y in self.detailed_versions} for x in [
                TrafficSplitStrategy.progressive, TrafficSplitStrategy.top_2,
                TrafficSplitStrategy.uniform]}
            for strategy in old_split:
                old_split[strategy][self.detailed_baseline_version.id] = 100

        logger.debug("Current split before")
        logger.debug(self.traffic_split_recommendation)

        for strategy in self.traffic_split_recommendation:  # for each strategy
            for candidate in self.detailed_candidate_versions:  # for each candidate
                increase = self.traffic_split_recommendation[strategy][candidate] - \
                    old_split[strategy][candidate]
                excess = max(
                    0, increase - self.eip.traffic_control.max_increment)
                # cap increase and add it to baseline
                self.traffic_split_recommendation[strategy][candidate] -= excess
                self.traffic_split_recommendation[strategy][self.detailed_baseline_version.id] += \
                    excess

        logger.debug("Old split")
        logger.debug(old_split)

        logger.debug("Current split after")
        logger.debug(self.traffic_split_recommendation)

    def assemble_assessment_and_recommendations(self):
        """Create and return the final assessment and recommendation
        """
        # get baseline and candidate assessments
        baseline_assessment = None
        candidate_assessments = []
        for version in self.detailed_versions.values():
            request_count = \
                version.metrics["counter_metrics"][ITER8_REQUEST_COUNT].aggregated_metric.value

            if version.is_baseline:
                baseline_assessment = VersionAssessment(
                    id=version.id,
                    request_count=request_count,
                    criterion_assessments=version.criterion_assessments,
                    win_probability=self.win_probababilities[version.id]
                )
            else:
                candidate_assessments.append(CandidateVersionAssessment(
                    id=version.id,
                    request_count=request_count,
                    criterion_assessments=version.criterion_assessments,
                    win_probability=self.win_probababilities[version.id]
                ))

        # get winner assessments

        wvf = False

        current_best_version = self.win_probababilities.index[np.argmax(
            self.win_probababilities)]
        probability_of_winning_for_best_version = self.win_probababilities[current_best_version]

        if probability_of_winning_for_best_version > \
                AdvancedParameters.min_posterior_probability_for_winner:
            wvf = True

        winner_assessment = WinnerAssessment(
            winning_version_found=wvf,
            current_best_version=current_best_version,
            probability_of_winning_for_best_version=probability_of_winning_for_best_version)

        logger.debug("Winner assessment")
        logger.debug(self.win_probababilities)
        logger.debug("%s, %s, %s", wvf, current_best_version,
                     probability_of_winning_for_best_version)

        # get final assessment and response
        it8ar = Iter8AssessmentAndRecommendation(** {
            "timestamp": datetime.now(),
            "baseline_assessment": baseline_assessment,
            "candidate_assessments": candidate_assessments,
            "traffic_split_recommendation": self.traffic_split_recommendation,
            "winner_assessment": winner_assessment,
            "status": [],
            "last_state": {
                "aggregated_counter_metrics": self.aggregated_counter_metrics,
                "aggregated_ratio_metrics": self.get_aggregated_ratio_metrics(),
                "ratio_max_mins": self.ratio_max_mins,
                "traffic_split_recommendation": self.traffic_split_recommendation
            }
        })
        return it8ar
