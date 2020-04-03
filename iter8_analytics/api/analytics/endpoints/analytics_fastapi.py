# Module dependencies
from fastapi import FastAPI, Body

# iter8 stuff
from iter8_analytics.api.analytics.response_hil import *
from iter8_analytics.api.analytics.request_parameters_hil import *

app = FastAPI()

# An example for swagger documentation
eip_example = {
    'start_time': "2020-04-03T12:55:50.568Z",
    "iter8_metrics": [
        {
            "id": "simple_ratio",
            "lower_is_better": True,
            "numerator_prom_query_template": "sum(of(parts)) > whole",
            "denomenator_prom_query_template": "whole > sum(or(parts))",
            "binary_metric": False
        },
        {
            "id": "simple_counter",
            "lower_is_better": True,
            "prom_query_template": "count(me_in)"
        }
    ],
    "assessment_criteria": [
        {
            "metric_id": "simple_ratio",
            "reward": False,
            "upper_threshold": {
                "threshold_type": "absolute",
                "value": 25
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "tags": {
            'service': "reviews",
            'deployment': "candid"
        }
    },
    "candidates": [
        {
            "id": "reviews_candidate",
            "tags": {
                'service': "reviews",
                'deployment': "candid"
            }
        }
    ],
    "advanced_traffic_control_parameters": {
        "exploration_traffic_percentage": 5.0,
        "check_and_increment_parameters": {
            "step_size": 1
        }
    },
    "advanced_assessment_parameters": {
        "posterior_probability_for_credible_intervals": 95.0,
        "min_posterior_probability_for_winner": 99.0
    }
}

ar_example = {
    'timestamp': "2020-04-03T12:59:50.568Z",
    'baseline_assessment': {
        "id": "reviews_base",
        "request_count": 500,
        "win_probability": 0.1,
        "metric_assessments": [
            {
                "id": "simple_ratio",
                "statistics": {
                    "value": 0.005,
                    "ratio_statistics": {
                        "sample_size": 500,
                        "improvement_over_baseline": {
                            'lower': 2.3,
                            'upper': 5.0
                        },
                        "probability_of_beating_baseline": .82,
                        "probability_of_being_best_version": 0.1,
                        "credible_interval": {
                            'lower': 22, 
                            'upper': 28
                        }
                    }
                },
                "threshold_assessment": {
                    "lower_threshold_breached": False,
                    "upper_threshold_breached": False,
                    "probability_of_satisfying_thresholds": 0.8
                }
            }
        ]
    },
    'candidate_assessments': [
        {
            "id": "reviews_candidate",
            "request_count": 1500,
            "win_probability": 0.11,
            "metric_assessments": [
                {
                    "id": "simple_ratio",
                    "statistics": {
                        "value": 0.1005,
                        "ratio_statistics": {
                            "sample_size": 1500,
                            "improvement_over_baseline": {
                                'lower': 12.3, 
                                'upper': 15.0
                            },
                            "probability_of_beating_baseline": .182,
                            "probability_of_being_best_version": 0.1,
                            "credible_interval": {
                                'lower': 122, 
                                'upper': 128
                            }
                        }
                    },
                    "threshold_assessment": {
                        "lower_threshold_breached": False,
                        "upper_threshold_breached": False,
                        "probability_of_satisfying_thresholds": 0.180
                    }
                }
            ]
        }
    ],
    'traffic_split_recommendation': {
        'unif': {
            'reviews_base': 50.0,
            'reviews_candidate': 50.0
        }
    },
    'winner_assessment': {
        'winning_version_found': False
    },
    'status': ["all_ok"]
}

@app.post("/assessment", response_model=Iter8AssessmentAndRecommendation)
def provide_assessment_for_this_experiment_iteration(eip: ExperimentIterationParameters = Body(..., example=eip_example)):
    """
      POST iter8 experiment iteration data and obtain assessment of how the versions are performing and recommendations on how to split traffic based on multiple strategies.
      """

    return Iter8AssessmentAndRecommendation(** ar_example)
