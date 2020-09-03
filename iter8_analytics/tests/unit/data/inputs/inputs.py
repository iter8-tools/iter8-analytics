import copy

eip_example = {
    'start_time': "2020-04-03T12:55:50.568Z",
    'iteration_number': 1,
    'service_name': "reviews",
    "metric_specs": {
        "counter_metrics": [
            {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            },
            {
                "id": "conversion_count",
                "query_template": "sum(increase(newsletter_signups[$interval])) by ($version_labels)"
            },
        ],
        "ratio_metrics": [
            {
                "id": "iter8_mean_latency",
                "numerator": "iter8_total_latency",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower",
                "zero_to_one": False
            },
            {
                "id": "iter8_error_rate",
                "numerator": "iter8_error_count",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower",
                "zero_to_one": True
            },
            {
                "id": "conversion_rate",
                "numerator": "conversion_count",
                "denominator": "iter8_request_count",
                "preferred_direction": "higher",
                "zero_to_one": True
            }
        ]},
    "criteria": [
        {
            "id": "0",
            "metric_id": "iter8_mean_latency",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 25
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "version_labels": {
            'destination_service_namespace': "default",
            'destination_workload': "reviews-v1"
        }
    },
    "candidates": [
        {
            "id": "reviews_candidate",
            "version_labels": {
                'destination_service_namespace': "default",
                'destination_workload': "reviews-v2"
            }
        }
    ]
}

ar_example = {
    'timestamp': "2020-04-03T12:59:50.568Z",
    'baseline_assessment': {
        "id": "reviews_base",
        "request_count": 500,
        "win_probability": 0.1,
        "criterion_assessments": [
            {
                "id": "0",
                "metric_id": "iter8_mean_latency",
                "statistics": {
                    "value": 0.005,
                    "ratio_statistics": {
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
            "criterion_assessments": [
                {
                    "id": "0",
                    "metric_id": "iter8_mean_latency",
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

reviews_example = {
    "start_time": "2020-05-17T12:55:50.568Z",
    "service_name": "reviews",
    "metric_specs": {
        "counter_metrics": [
            {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            }
        ],
        "ratio_metrics": [
            {
                "id": "iter8_mean_latency",
                "numerator": "iter8_total_latency",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower"
            }
        ]
    },
    "criteria": [
        {
            "id": "0",
            "metric_id": "iter8_error_count",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 25
            }
        },
        {
            "id": "1",
            "metric_id": "iter8_mean_latency",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 500
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "version_labels": {
            "destination_service_namespace": "bookinfo-iter8",
            "destination_workload": "reviews-v2"
        }
    },
    "candidates": [
        {
            "id": "reviews_candidate",
            "version_labels": {
                "destination_service_namespace": "bookinfo-iter8",
                "destination_workload": "reviews-v3"
            }
        }
    ]
}



last_state = {
    "aggregated_counter_metrics": {
        "reviews_candidate": {
            "iter8_request_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_error_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_total_latency": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        },
        "reviews_base": {
            "iter8_request_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_error_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_total_latency": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        }
    },
    "aggregated_ratio_metrics": {
        "reviews_candidate": {
            "iter8_mean_latency": {
                "value": None,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        },
        "reviews_base": {
            "iter8_mean_latency": {
                "value": None,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        }
    },
    "ratio_max_mins": {
        "iter8_mean_latency": {
            "minimum": None,
            "maximum": None
        }
    }
}

partial_last_state = {
    "aggregated_counter_metrics": {
        "reviews_candidate": {
            "iter8_request_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_error_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        },
        "reviews_base": {
            "iter8_request_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_error_count": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            },
            "iter8_total_latency": {
                "value": 0,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        }
    },
    "aggregated_ratio_metrics": {
        "reviews_candidate": {
            "iter8_mean_latency": {
                "value": None,
                "timestamp": "2020-05-19T11:41:51.474487+00:00",
                "status": "no versions in prometheus response"
            }
        }
    },
    "ratio_max_mins": {
        "iter8_mean_latency": {
            "minimum": None,
            "maximum": None
        }
    }
}

last_state_with_ratio_max_mins = copy.deepcopy(last_state)
last_state_with_ratio_max_mins["ratio_max_mins"] = {
    "iter8_mean_latency": {
        "minimum": 1.5,
        "maximum": 20
    }
}

reviews_example_with_last_state = {
    "start_time": "2020-05-17T12:55:50.568Z",
    "service_name": "reviews",
    "metric_specs": {
        "counter_metrics": [
            {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            }
        ],
        "ratio_metrics": [
            {
                "id": "iter8_mean_latency",
                "numerator": "iter8_total_latency",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower"
            }
        ]
    },
    "criteria": [
        {
            "id": "0",
            "metric_id": "iter8_error_count",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 25
            }
        },
        {
            "id": "1",
            "metric_id": "iter8_mean_latency",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 500
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "version_labels": {
            "destination_service_namespace": "bookinfo-iter8",
            "destination_workload": "reviews-v2"
        }
    },
    "candidates": [
        {
            "id": "reviews_candidate",
            "version_labels": {
                "destination_service_namespace": "bookinfo-iter8",
                "destination_workload": "reviews-v3"
            }
        }
    ],
    "last_state": copy.deepcopy(last_state)
}

reviews_example_with_partial_last_state = copy.deepcopy(
    reviews_example_with_last_state)
reviews_example_with_partial_last_state["last_state"] = copy.deepcopy(
    partial_last_state)

reviews_example_with_ratio_max_mins = copy.deepcopy(
    reviews_example_with_last_state)
reviews_example_with_ratio_max_mins["last_state"] = copy.deepcopy(
    last_state_with_ratio_max_mins)

eip_with_invalid_ratio = copy.deepcopy(reviews_example_with_ratio_max_mins)
eip_with_invalid_ratio["metric_specs"]["ratio_metrics"].append({
    "id": "iter8_invalid_latency",
    "numerator": "iter8_total_invalid_latency",
    "denominator": "iter8_request_count",
    "preferred_direction": "lower"
})
eip_with_invalid_ratio["criteria"].append({
    "id": "2",
    "metric_id": "iter8_invalid_latency",
    "is_reward": False,
    "threshold": {
          "type": "absolute",
          "value": 500
    }
})

eip_with_unknown_metric_in_criterion = copy.deepcopy(
    reviews_example_with_ratio_max_mins)
eip_with_unknown_metric_in_criterion["criteria"].append({
    "id": "2",
    "metric_id": "iter8_invalid_latency",
    "is_reward": False,
    "threshold": {
          "type": "absolute",
          "value": 500
    }
})


eip_with_percentile = {
    "name": "productpage-abn-test",
    "start_time": "2020-07-17T20:05:02-04:00",
    "service_name": "productpage",
    "iteration_number": 1,
    "metric_specs": {
        "counter_metrics": [{
            "name": "iter8_request_count",
            "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
        }, {
            "name": "iter8_total_latency",
            "query_template": "(sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels))"
        }, {
            "name": "iter8_error_count",
            "preferred_direction": "lower",
            "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)"
        }, {
            "name": "books_purchased_total",
            "preferred_direction": "higher",
            "query_template": "sum(increase(number_of_books_purchased_total{}[$interval])) by ($version_labels)"
        }, {
            "name": "500_ms_latency_count",
            "preferred_direction": "higher",
            "query_template": "(sum(increase(istio_request_duration_milliseconds_bucket{le='500',reporter='source'}[$interval])) by ($version_labels))"
        }],
        "ratio_metrics": [{
            "name": "iter8_mean_latency",
            "numerator": "iter8_total_latency",
            "denominator": "iter8_request_count",
            "preferred_direction": "lower"
        }, {
            "name": "iter8_error_rate",
            "numerator": "iter8_error_count",
            "denominator": "iter8_request_count",
            "preferred_direction": "lower",
            "zero_to_one": True
        }, {
            "name": "mean_books_purchased",
            "numerator": "books_purchased_total",
            "denominator": "iter8_request_count",
            "preferred_direction": "higher"
        }, {
            "name": "500_ms_latency_percentile",
            "numerator": "500_ms_latency_count",
            "denominator": "iter8_request_count",
            "preferred_direction": "higher",
            "zero_to_one": True
        }]
    },
    "criteria": [{
        "id": "0",
        "metric_id": "500_ms_latency_percentile",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.99
        }
    }, {
        "id": "1",
        "metric_id": "iter8_error_rate",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.0001
        }
    }],
    "baseline": {
        "id": "productpage-v1",
        "version_labels": {
            "destination_service_namespace": "kubecon-demo",
            "destination_workload": "productpage-v1"
        }
    },
    "candidates": [{
        "id": "productpage-v2",
        "version_labels": {
            "destination_service_namespace": "kubecon-demo",
            "destination_workload": "productpage-v2"
        }
    }, {
        "id": "productpage-v3",
        "version_labels": {
            "destination_service_namespace": "kubecon-demo",
            "destination_workload": "productpage-v3"
        }
    }],
    "last_state": {},
    "traffic_control": {
        "max_increment": 2,
        "strategy": "progressive"
    }
}

reviews_example_without_request_count = copy.deepcopy(reviews_example)
del reviews_example_without_request_count["criteria"][1]
del reviews_example_without_request_count["metric_specs"]["counter_metrics"][0]
del reviews_example_without_request_count["metric_specs"]["ratio_metrics"][0]

eip_with_assessment = {
    "name": "productpage-abn-test",
    "start_time": "2020-07-20T17:19:13-04:00",
    "service_name": "productpage",
    "iteration_number": 17,
    "metric_specs": {
        "counter_metrics": [{
            "name": "iter8_request_count",
            "query_template": "sum(increase(istio_requests_total{reporter='source',job='istio-mesh'}[$interval])) by ($version_labels)"
        }, {
            "name": "iter8_total_latency",
            "query_template": "(sum(increase(istio_request_duration_seconds_sum{reporter='source',job='istio-mesh'}[$interval])) by ($version_labels))*1000"
        }, {
            "name": "iter8_error_count",
            "preferred_direction": "lower",
            "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source',job='istio-mesh'}[$interval])) by ($version_labels)"
        }, {
            "name": "books_purchased_total",
            "query_template": "sum(increase(number_of_books_purchased_total{}[$interval])) by ($version_labels)"
        }, {
            "name": "le_500_ms_latency_request_count",
            "query_template": "(sum(increase(istio_request_duration_seconds_bucket{le='0.5',reporter='source',job='istio-mesh'}[$interval])) by ($version_labels))"
        }],
        "ratio_metrics": [{
            "name": "iter8_mean_latency",
            "numerator": "iter8_total_latency",
            "denominator": "iter8_request_count",
            "preferred_direction": "lower"
        }, {
            "name": "iter8_error_rate",
            "numerator": "iter8_error_count",
            "denominator": "iter8_request_count",
            "zero_to_one": True,
            "preferred_direction": "lower"
        }, {
            "name": "mean_books_purchased",
            "numerator": "books_purchased_total",
            "denominator": "iter8_request_count",
            "preferred_direction": "higher"
        }, {
            "name": "500_ms_latency_percentile",
            "numerator": "le_500_ms_latency_request_count",
            "denominator": "iter8_request_count",
            "zero_to_one": True,
            "preferred_direction": "higher"
        }]
    },
    "criteria": [{
        "id": "iter8_mean_latency",
        "metric_id": "iter8_mean_latency",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 1500
        }
    }, {
        "id": "iter8_error_rate",
        "metric_id": "iter8_error_rate",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.05
        }
    }, {
        "id": "500_ms_latency_percentile",
        "metric_id": "500_ms_latency_percentile",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.9
        }
    }, {
        "id": "mean_books_purchased",
        "metric_id": "mean_books_purchased",
        "is_reward": True
    }],
    "baseline": {
        "id": "productpage-v1",
        "version_labels": {
            "destination_workload": "productpage-v1",
            "destination_workload_namespace": "kubecon-demo"
        }
    },
    "candidates": [{
        "id": "productpage-v2",
        "version_labels": {
            "destination_workload": "productpage-v2",
            "destination_workload_namespace": "kubecon-demo"
        }
    }, {
        "id": "productpage-v3",
        "version_labels": {
            "destination_workload": "productpage-v3",
            "destination_workload_namespace": "kubecon-demo"
        }
    }],
    "last_state": {
        "aggregated_counter_metrics": {
            "productpage-v1": {
                "books_purchased_total": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.001436+00:00",
                    "value": 2675.060869565217
                },
                "iter8_error_count": {
                    "status": "no versions in prometheus response",
                    "timestamp": "2020-07-20T21:25:00.726973+00:00",
                    "value": 0
                },
                "iter8_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.500394+00:00",
                    "value": 1100.9376796274955
                },
                "iter8_total_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.608216+00:00",
                    "value": 116867.79877397961
                },
                "le_500_ms_latency_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.880245+00:00",
                    "value": 1066.2376477633036
                }
            },
            "productpage-v2": {
                "books_purchased_total": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.001436+00:00",
                    "value": 43495.340441392604
                },
                "iter8_error_count": {
                    "status": "no versions in prometheus response",
                    "timestamp": "2020-07-20T21:25:00.726973+00:00",
                    "value": 0
                },
                "iter8_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.500394+00:00",
                    "value": 1103.040681252753
                },
                "iter8_total_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.608216+00:00",
                    "value": 1513982.9278989176
                },
                "le_500_ms_latency_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.880245+00:00",
                    "value": 270.2396902763801
                }
            },
            "productpage-v3": {
                "books_purchased_total": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.001436+00:00",
                    "value": 15931.255805285438
                },
                "iter8_error_count": {
                    "status": "no versions in prometheus response",
                    "timestamp": "2020-07-20T21:25:00.726973+00:00",
                    "value": 0
                },
                "iter8_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.500394+00:00",
                    "value": 1084.1133447970965
                },
                "iter8_total_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.608216+00:00",
                    "value": 98910.32374279092
                },
                "le_500_ms_latency_request_count": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:00.880245+00:00",
                    "value": 1074.6497084334599
                }
            }
        },
        "aggregated_ratio_metrics": {
            "productpage-v1": {
                "500_ms_latency_percentile": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.488586+00:00",
                    "value": 0.9684813840907572
                },
                "iter8_error_rate": {
                    "status": "zeroed ratio",
                    "timestamp": "2020-07-20T21:25:01.342217+00:00",
                    "value": 0
                },
                "iter8_mean_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.118267+00:00",
                    "value": 106.15296481951826
                },
                "mean_books_purchased": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.617785+00:00",
                    "value": 2.422820076378882
                }
            },
            "productpage-v2": {
                "500_ms_latency_percentile": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.488586+00:00",
                    "value": 0.24499521628654852
                },
                "iter8_error_rate": {
                    "status": "zeroed ratio",
                    "timestamp": "2020-07-20T21:25:01.342217+00:00",
                    "value": 0
                },
                "iter8_mean_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.118267+00:00",
                    "value": 1372.5540260033258
                },
                "mean_books_purchased": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.617785+00:00",
                    "value": 39.38968647171404
                }
            },
            "productpage-v3": {
                "500_ms_latency_percentile": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.488586+00:00",
                    "value": 0.9912706209096545
                },
                "iter8_error_rate": {
                    "status": "zeroed ratio",
                    "timestamp": "2020-07-20T21:25:01.342217+00:00",
                    "value": 0
                },
                "iter8_mean_latency": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.118267+00:00",
                    "value": 91.23614631023943
                },
                "mean_books_purchased": {
                    "status": "all_ok",
                    "timestamp": "2020-07-20T21:25:01.617785+00:00",
                    "value": 14.679574964516965
                }
            }
        },
        "ratio_max_mins": {
            "500_ms_latency_percentile": {
                "maximum": 0.9912706209096545,
                "minimum": 0.16666650018723458
            },
            "iter8_error_rate": {
                "maximum": 0,
                "minimum": 0
            },
            "iter8_mean_latency": {
                "maximum": 1507.8847318570406,
                "minimum": 91.23614631023943
            },
            "mean_books_purchased": {
                "maximum": 39.693079869958254,
                "minimum": 2.2894643119744784
            }
        }
    },
    "traffic_control": {
        "max_increment": 25,
        "strategy": "progressive"
    }
}

eip_with_relative_assessments = {
    "name": "productpage-abn-test",
    "start_time": "2020-07-20T17:19:13-04:00",
    "service_name": "productpage",
    "iteration_number": 10,
    "metric_specs": {
        "counter_metrics": [{
            "name": "iter8_request_count",
            "query_template": "sum(increase(istio_requests_total{reporter='source',job='istio-mesh'}[$interval])) by ($version_labels)"
        }, {
            "name": "iter8_total_latency",
            "query_template": "(sum(increase(istio_request_duration_seconds_sum{reporter='source',job='istio-mesh'}[$interval])) by ($version_labels))*1000"
        }, {
            "name": "iter8_error_count",
            "preferred_direction": "lower",
            "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source',job='istio-mesh'}[$interval])) by ($version_labels)"
        }, {
            "name": "books_purchased_total",
            "query_template": "sum(increase(number_of_books_purchased_total{}[$interval])) by ($version_labels)"
        }, {
            "name": "le_500_ms_latency_request_count",
            "query_template": "(sum(increase(istio_request_duration_seconds_bucket{le='0.5',reporter='source',job='istio-mesh'}[$interval])) by ($version_labels))"
        }, {
            "name": "le_inf_latency_request_count",
            "query_template": "(sum(increase(istio_request_duration_seconds_bucket{le='+Inf',reporter='source',job='istio-mesh'}[$interval])) by ($version_labels))"
        }],
        "ratio_metrics": [{
            "name": "iter8_mean_latency",
            "numerator": "iter8_total_latency",
            "denominator": "iter8_request_count",
            "preferred_direction": "lower"
        }, {
            "name": "iter8_error_rate",
            "numerator": "iter8_error_count",
            "denominator": "iter8_request_count",
            "zero_to_one": True,
            "preferred_direction": "lower"
        }, {
            "name": "mean_books_purchased",
            "numerator": "books_purchased_total",
            "denominator": "iter8_request_count",
            "preferred_direction": "higher"
        }, {
            "name": "500_ms_latency_percentile",
            "numerator": "le_500_ms_latency_request_count",
            "denominator": "le_inf_latency_request_count",
            "zero_to_one": True,
            "preferred_direction": "higher"
        }]
    },
    "criteria": [{
        "id": "0",
        "metric_id": "iter8_mean_latency",
        "is_reward": False,
        "threshold": {
            "threshold_type": "relative",
            "value": 1.6
        }
    }, {
        "id": "1",
        "metric_id": "iter8_error_rate",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.05
        }
    }, {
        "id": "2",
        "metric_id": "500_ms_latency_percentile",
        "is_reward": False,
        "threshold": {
            "threshold_type": "absolute",
            "value": 0.9
        }
    }, {
        "id": "3",
        "metric_id": "mean_books_purchased",
        "is_reward": True
    }],
    "baseline": {
        "id": "productpage-v1",
        "version_labels": {
            "destination_workload": "productpage-v1",
            "destination_workload_namespace": "kubecon-demo"
        }
    },
    "candidates": [{
        "id": "productpage-v2",
        "version_labels": {
            "destination_workload": "productpage-v2",
            "destination_workload_namespace": "kubecon-demo"
        }
    }, {
        "id": "productpage-v3",
        "version_labels": {
            "destination_workload": "productpage-v3",
            "destination_workload_namespace": "kubecon-demo"
        }
    }],
    "last_state": {
        "aggregated_counter_metrics": {
            "productpage-v2": {
                "iter8_request_count": {
                    "value": 182.72228233137372,
                    "timestamp": "2020-07-24T19:06:46.480713+00:00",
                    "status": "all_ok"
                },
                "iter8_total_latency": {
                    "value": 46004.62497939324,
                    "timestamp": "2020-07-24T19:06:46.651545+00:00",
                    "status": "all_ok"
                },
                "iter8_error_count": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:46.761778+00:00",
                    "status": "no versions in prometheus response"
                },
                "le_500_ms_latency_request_count": {
                    "value": 142.99993165455655,
                    "timestamp": "2020-07-24T19:06:46.866789+00:00",
                    "status": "all_ok"
                },
                "le_inf_latency_request_count": {
                    "value": 183.0447820092769,
                    "timestamp": "2020-07-24T19:06:46.970240+00:00",
                    "status": "all_ok"
                },
                "books_purchased_total": {
                    "value": 7574.673001453327,
                    "timestamp": "2020-07-24T19:06:47.083212+00:00",
                    "status": "all_ok"
                }
            },
            "productpage-v3": {
                "iter8_request_count": {
                    "value": 250.8062866067991,
                    "timestamp": "2020-07-24T19:06:46.480713+00:00",
                    "status": "all_ok"
                },
                "iter8_total_latency": {
                    "value": 8916.643818970602,
                    "timestamp": "2020-07-24T19:06:46.651545+00:00",
                    "status": "all_ok"
                },
                "iter8_error_count": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:46.761778+00:00",
                    "status": "no versions in prometheus response"
                },
                "le_500_ms_latency_request_count": {
                    "value": 251.24778563480407,
                    "timestamp": "2020-07-24T19:06:46.866789+00:00",
                    "status": "all_ok"
                },
                "le_inf_latency_request_count": {
                    "value": 251.37112870529108,
                    "timestamp": "2020-07-24T19:06:46.970240+00:00",
                    "status": "all_ok"
                },
                "books_purchased_total": {
                    "value": 3749.5571026679177,
                    "timestamp": "2020-07-24T19:06:47.083212+00:00",
                    "status": "all_ok"
                }
            },
            "productpage-v1": {
                "iter8_request_count": {
                    "value": 297.23328959973264,
                    "timestamp": "2020-07-24T19:06:46.480713+00:00",
                    "status": "all_ok"
                },
                "iter8_total_latency": {
                    "value": 9922.352942341287,
                    "timestamp": "2020-07-24T19:06:46.651545+00:00",
                    "status": "all_ok"
                },
                "iter8_error_count": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:46.761778+00:00",
                    "status": "no versions in prometheus response"
                },
                "le_500_ms_latency_request_count": {
                    "value": 297.23328959973264,
                    "timestamp": "2020-07-24T19:06:46.866789+00:00",
                    "status": "all_ok"
                },
                "le_inf_latency_request_count": {
                    "value": 297.23328959973264,
                    "timestamp": "2020-07-24T19:06:46.970240+00:00",
                    "status": "all_ok"
                },
                "books_purchased_total": {
                    "value": 765.8520108620773,
                    "timestamp": "2020-07-24T19:06:47.083212+00:00",
                    "status": "all_ok"
                }
            }
        },
        "aggregated_ratio_metrics": {
            "productpage-v2": {
                "iter8_mean_latency": {
                    "value": 251.62472741382498,
                    "timestamp": "2020-07-24T19:06:47.199408+00:00",
                    "status": "all_ok"
                },
                "iter8_error_rate": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:47.316578+00:00",
                    "status": "zeroed ratio"
                },
                "500_ms_latency_percentile": {
                    "value": 0.7815247494177242,
                    "timestamp": "2020-07-24T19:06:47.425152+00:00",
                    "status": "all_ok"
                },
                "mean_books_purchased": {
                    "value": 41.262452494397415,
                    "timestamp": "2020-07-24T19:06:47.535450+00:00",
                    "status": "all_ok"
                }
            },
            "productpage-v3": {
                "iter8_mean_latency": {
                    "value": 35.5249257408403,
                    "timestamp": "2020-07-24T19:06:47.199408+00:00",
                    "status": "all_ok"
                },
                "iter8_error_rate": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:47.316578+00:00",
                    "status": "zeroed ratio"
                },
                "500_ms_latency_percentile": {
                    "value": 1.0,
                    "timestamp": "2020-07-24T19:06:47.425152+00:00",
                    "status": "all_ok"
                },
                "mean_books_purchased": {
                    "value": 14.906850702730225,
                    "timestamp": "2020-07-24T19:06:47.535450+00:00",
                    "status": "all_ok"
                }
            },
            "productpage-v1": {
                "iter8_mean_latency": {
                    "value": 33.382374348792354,
                    "timestamp": "2020-07-24T19:06:47.199408+00:00",
                    "status": "all_ok"
                },
                "iter8_error_rate": {
                    "value": 0.0,
                    "timestamp": "2020-07-24T19:06:47.316578+00:00",
                    "status": "zeroed ratio"
                },
                "500_ms_latency_percentile": {
                    "value": 1.0,
                    "timestamp": "2020-07-24T19:06:47.425152+00:00",
                    "status": "all_ok"
                },
                "mean_books_purchased": {
                    "value": 2.565821648611445,
                    "timestamp": "2020-07-24T19:06:47.535450+00:00",
                    "status": "all_ok"
                }
            }
        },
        "ratio_max_mins": {
            "iter8_mean_latency": {
                "minimum": 26.50646096293112,
                "maximum": 251.62472741382498
            },
            "iter8_error_rate": {
                "minimum": 0.0,
                "maximum": 0.0
            },
            "500_ms_latency_percentile": {
                "minimum": 0.7733402047764519,
                "maximum": 1.0
            },
            "mean_books_purchased": {
                "minimum": 0.0,
                "maximum": 70.77637942479375
            }
        },
        "traffic_split_recommendation": {
            "progressive": {
                "productpage-v2": 32,
                "productpage-v3": 35,
                "productpage-v1": 33
            },
            "top_2": {
                "productpage-v2": 34,
                "productpage-v3": 33,
                "productpage-v1": 33
            },
            "uniform": {
                "productpage-v2": 34,
                "productpage-v3": 33,
                "productpage-v1": 33
            }
        }
    },
    "traffic_control": {
        "max_increment": 25,
        "strategy": "progressive"
    }
}

reviews_example_aa = {
    "start_time": "2020-05-17T12:55:50.568Z",
    "service_name": "reviews",
    "metric_specs": {
        "counter_metrics": [
            {
                "id": "iter8_request_count",
                "query_template": "sum(increase(istio_requests_total{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_total_latency",
                "query_template": "sum(increase(istio_request_duration_milliseconds_sum{reporter='source'}[$interval])) by ($version_labels)"
            },
            {
                "id": "iter8_error_count",
                "query_template": "sum(increase(istio_requests_total{response_code=~'5..',reporter='source'}[$interval])) by ($version_labels)",
                "preferred_direction": "lower"
            }
        ],
        "ratio_metrics": [
            {
                "id": "iter8_mean_latency",
                "numerator": "iter8_total_latency",
                "denominator": "iter8_request_count",
                "preferred_direction": "lower"
            }
        ]
    },
    "criteria": [
        {
            "id": "0",
            "metric_id": "iter8_mean_latency",
            "is_reward": False,
            "threshold": {
                "type": "absolute",
                "value": 500
            }
        }
    ],
    "baseline": {
        "id": "reviews_base",
        "version_labels": {
            "destination_service_namespace": "default",
            "destination_workload": "reviews-v1"
        }
    },
    "candidates": [
        {
            "id": "reviews_candidate",
            "version_labels": {
                "destination_service_namespace": "default",
                "destination_workload": "reviews-v1"
            }
        }
    ]
}

