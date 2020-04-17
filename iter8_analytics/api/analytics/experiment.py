"""
Class and methods to run an iteration of an iter8 eperiment, and return assessment and recommendations
"""

from iter8_analytics.api.analytics.experiment_iteration_request import ExperimentIterationParameters, RatioMetricSpec

from iter8_analytics.api.analytics.experiment_iteration_response import Iter8AssessmentAndRecommendation

from iter8_analytics.api.analytics.endpoints.examples import ar_example

from iter8_analytics.api.analytics.metrics import *

class Experiment():
    """The main experiment class"""

    def __init__(self, eip: ExperimentIterationParameters):  
        self.eip = eip

    def run(self) -> Iter8AssessmentAndRecommendation:
        """Perform a single iteration of the experiment and output assessment and recommendation"""  

        self.update_metrics()
        self.update_beliefs()
        self.create_posterior_samples()
        self.create_candidate_assessments()
        self.create_winner_assessments()
        self.create_traffic_recommendations()
        return self.assemble_assessment_and_recommendations()

    def update_metrics(self):
        """Query prometheus to update sufficient stats and metrics. Prometheus instance creation, and all prometheus related errors are detected and the relevant status codes are populated here..."""
        old_sufficient_stats = self.eip.last_state.sufficient_stats if self.eip.last_state else None
        new_sufficient_stats = get_sufficient_stats(self.eip)
        self.sufficient_stats = aggregate_sufficient_stats(old_sufficient_stats, new_sufficient_stats)
        self.metrics = get_metrics_from_stats(self.sufficient_stats)

    def update_beliefs(self):
        """Update beliefs for ratio metrics. This will internally use sufficient stats. If belief update is not possible due to insufficient data, then the relevant status codes are populated here"""
        versions = self.eip.candidates + [self.eip.baseline]
        for version in versions:
            for metric_spec in self.eip.metric_specs: 
                if isinstance(metric_spec, RatioMetricSpec):
                    self.update_belief_for_metric(version)

    def update_belief_for_metric(self, version, metric_spec):
        """Update belief for a given ratio metric. If belief update is not possible due to insufficient data, then the relevant status codes are populated here"""
        assert(isinstance(metric_spec, RatioMetricSpec))
        pass

    def create_posterior_samples(self):
        """These samples are used for assessment and traffic routing"""
        self.create_ratio_metric_samples()
        self.create_utility_samples()

    def create_ratio_metric_samples(self):
        """These samples are used for assessment and traffic routing"""
        pass

    def create_utility_samples(self):
        """These samples are used for assessment and traffic routing"""
        pass

    def create_candidate_assessments(self):
        """Create candidate assessments for each metric and also overall assessment. If assessment cannot be created due to insufficient data, then the relevant status codes are populated"""
        pass

    def create_winner_assessments(self):
        """Create winner assessment. If winner cannot be created due to insufficient data, then the relevant status codes are populated"""
        pass

    def create_traffic_recommendations(self):
        """Create traffic recommendations for individual algorithms"""
        self.create_epsilon_greedy_recommendation()
        self.create_pbr_recommendation() # PBR  = posterior Bayesian sampling
        self.create_top_2_pbr_recommendation()
        self.mix_recommendations() # after taking into account step size and current split

    def create_epsilon_greedy_recommendation(self):
        pass

    def create_pbr_recommendation(self):
        pass

    def create_top_2_pbr_recommendation(self):
        pass

    def mix_recommendations(self):
        """Create the final traffic recommendation"""
        pass

    def assemble_assessment_and_recommendations(self):
        """Create and return the final assessment and recommendation"""
        return Iter8AssessmentAndRecommendation(** ar_example)

