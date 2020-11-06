"""
Module containing classes and methods for querying prometheus and returning metric data.
"""

from iter8_analytics.api.v2.types import ExperimentResourceAndMetricResources, \
    Iter8v2AggregatedMetrics

def get_aggregated_metrics(ermr: ExperimentResourceAndMetricResources):
    """
    Get aggregated metrics from experiment resource and metric resources.
    """
    iam = Iter8v2AggregatedMetrics(data = [{
        'name': 'request-count',
        'max': 25,
        'min': 8,
        'versions': [
            {
                'name': 'baseline',
                'max': 25,
                'min': 0,
                'value': 25
            }, {
                'name': 'canary',
                'max': 15,
                'min': 0,
                'value': 15
            }
        ]
    }], message = "all ok")
    return iam
    