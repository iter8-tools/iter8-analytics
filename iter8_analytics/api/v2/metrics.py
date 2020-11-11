"""
Module containing classes and methods for querying prometheus and returning metric data.
"""
# core python dependencies
from datetime import datetime, timezone
import logging
from string import Template
import numbers

# external module dependencies
import requests
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import jq

# iter8 dependencies
from iter8_analytics.api.v2.types import ExperimentResourceAndMetricResources, \
    AggregatedMetrics, MetricResource, Version, AggregatedMetric, VersionMetric
import iter8_analytics.constants as constants
from iter8_analytics.config import env_config

logger = logging.getLogger('iter8_analytics')

def get_metrics_url_template(metric_resource):
    """
    Get the URL template for the given metric.
    """
    assert metric_resource.spec.provider == "prometheus"
    prometheus_url_template = env_config[constants.METRICS_BACKEND_CONFIG_URL]
    return prometheus_url_template + "/api/v1/query"

def extrapolate(template: str, version: Version, start_time: datetime):
    """
    Extrapolate a string templated using name and tags of versions,
    and starting time of the experiment
    """
    args = {}
    args["name"] = version.name
    for key, value in version.tags.items():
        args[key] = value
    args["interval"] = int((datetime.now(timezone.utc) - start_time).total_seconds())
    args["interval"] = str(args["interval"]) + 's'
    templ = Template(template)
    return templ.substitute(**args)

def unmarshal(response, provider):
    """
    Unmarshal value from metric response
    """
    assert provider == "prometheus"
    # for now, this will hardcode the prometheus unmarshaler
    schema = {
        "name": "prometheus_singleton_vector",
        "data": {
                "$schema": "http://json-schema.org/schema#",
                "$id": "http://iter8.tools/kfserving/schemas/prometheus_singleton.json",
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "success"
                        ]
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "resultType": {
                                "type": "string",
                                "enum": [
                                    "vector"
                                ]
                            },
                            "result": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {
                                            "type": "array",
                                            "minItems": 2,
                                            "maxItems": 2
                                        }
                                    },
                                    "required": ["value"]
                                },
                                "minItems": 1,
                                "maxItems": 1
                            }
                        },
                        "required": ["resultType", "result"]
                    }
                },
            "required": [
                    "status",
                    "data"
                ]
        }
    }
    try:
        validate(instance = response, schema = schema)
        logger.info(f"Validated response: {response}")
        try:
            num = jq.compile(".data.result[0].value[1] | tonumber").input(response).first()
            if isinstance(num, numbers.Number):
                return num, None
            return None, ValueError("Metrics response did not yield a number")
        except Exception as err:
            return None, err
    except ValidationError as err:
        return None, err

def get_metric_value(metric_resource: MetricResource, version: Version, start_time: datetime):
    """
    Extrapolate metrics backend URL and query parameters; query the metrics backend;
    and return the value of the metric.
    """
    url_template = get_metrics_url_template(metric_resource)
    url = extrapolate(url_template, version, start_time)
    # example for prometheus; 
    # metric_resource.spec.params now: {"query": "your prometheus query template"}
    params = {}
    for pt_key, pt_value in metric_resource.spec.params.items():
        params[pt_key] = extrapolate(pt_value, version, start_time)
    # continuing the above example...
    # params now: {"query": "your prometheus query"}
    (value, err) = (None, None)
    try:
        response = requests.get(url, params=params).json()
    except Exception as exp:
        logger.error("Error while attempting to connect to metrics backend")
        return value, exp
    value, err = unmarshal(response, metric_resource.spec.provider)
    return value, err

def get_aggregated_metrics(ermr: ExperimentResourceAndMetricResources):
    """
    Get aggregated metrics from experiment resource and metric resources.
    """
    versions = [ermr.experimentResource.spec.versionInfo.baseline]
    versions += ermr.experimentResource.spec.versionInfo.candidates

    messages = []

    def collect_messages_and_log(message: str):
        messages.append(message)
        logger.error(message)

    iam = AggregatedMetrics(data = {})

    for metric_resource in ermr.metricResources:
        iam.data[metric_resource.metadata.name] = AggregatedMetric(data = {})
        for version in versions:
            iam.data[metric_resource.metadata.name].data[version.name] = VersionMetric()
            val, err = get_metric_value(metric_resource, version, \
            ermr.experimentResource.status.startTime)
            if err is None:
                iam.data[metric_resource.metadata.name].data[version.name].value = val
            else:
                collect_messages_and_log(err.message)
    if messages:
        iam.message = "warnings: " + ', '.join(messages)
    else:
        iam.message = "all ok"
    logger.info(iam)
    return iam
