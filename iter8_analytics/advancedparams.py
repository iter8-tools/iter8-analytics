"""Advanced Parameters that control the behavior of iter8 analytics"""

class AdvancedParameters:
    """Globally defined constants for experiment"""
    # 5% of traffic always used for exploration
    exploration_traffic_percentage = 5.0
    posterior_probability_for_credible_intervals = 0.95
    # no winner until iter8 is 99% confident
    min_posterior_probability_for_winner = 0.99
    # a higher value of this factor encourages greater exploration
    variance_boost_factor = 1.0