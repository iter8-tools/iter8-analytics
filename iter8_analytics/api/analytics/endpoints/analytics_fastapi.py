# Module dependencies
from fastapi import FastAPI, Body

# iter8 stuff
from iter8_analytics.api.analytics.response_hil import *
from iter8_analytics.api.analytics.request_parameters_hil import *

app = FastAPI()

# An example for swagger documentation
eip_example = {
    'start_time': "2020-04-03T12:55:50.568Z",
    "metric_specs": {
        "counter_metrics": [
        {
            "id": "iter8_request_count",
            "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($entity_labels)"
        },
        {
            "id": "iter8_total_latency",
            "query_template": "sum(increase(istio_request_duration_seconds_sum{reporter='source'}[$interval]$offset_str)) by ($entity_labels)"
        },
        {
            "id": "iter8_error_count",
            "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($entity_labels)",
            "preferred_direction": "lower"
        },
        {
            "id": "conversion_count",
            "query_template": "sum(increase(newsletter_signups[$interval])) by ($entity_labels)"
        },
    ],  
    "ratio_metrics": [
        {
            "id": "iter8_mean_latency",
            "numerator": "iter8_total_latency",
            "denomenator": "iter8_request_count",
            "preferred_direction": "lower",
            "unit_range": False
        }, 
        {
            "id": "iter8_error_rate",
            "numerator": "iter8_error_count",
            "denomenator": "iter8_request_count",
            "preferred_direction": "lower",
            "unit_range": True
        }, 
        {
            "id": "conversion_rate",
            "numerator": "conversion_count",
            "denomenator": "iter8_request_count",
            "preferred_direction": "higher",
            "unit_range": True
        }
    ]},
    "assessment_criteria": [
        {
            "metric_id": "iter8_mean_latency",
            "reward": False,
            "threshold": {
                "threshold_type": "absolute",
                "value": 25
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "tags": {
            'service': "reviews",
            'deployment': "baseline"
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
                "id": "iter8_mean_latency",
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
                    "threshold_breached": False,
                    "probability_of_satisfying_threshold": 0.8
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
                    "id": "iter8_mean_latency",
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
                        "threshold_breached": True,
                        "probability_of_satisfying_threshold": 0.180
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
