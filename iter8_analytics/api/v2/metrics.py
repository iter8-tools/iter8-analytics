"""
Module containing classes and methods for querying prometheus and returning metric data.
"""
# core python dependencies
from datetime import datetime, timezone
import logging
from string import Template
import numbers
import pprint

# external module dependencies
import requests
import numpy as np
import jq

# iter8 dependencies
from iter8_analytics.api.v2.types import AggregatedMetricsAnalysis, ExperimentResource, \
    MetricResource, VersionDetail, AggregatedMetric, VersionMetric
import iter8_analytics.config as config
from iter8_analytics.api.utils import Message, MessageLevel

logger = logging.getLogger('iter8_analytics')


def get_metrics_url_template(metric_resource):
    """
    Get the URL template for the given metric.
    """
    return metric_resource.spec.urlTemplate

def extrapolate(template: str, version: VersionDetail, start_time: datetime):
    """
    Extrapolate a string templated using name and tags of versions,
    and starting time of the experiment
    """
    args = {}
    args["name"] = version.name
    if version.variables is not None and len(version.variables) > 0:
        for variable in version.variables:
            args[variable.name] = variable.value
    args["interval"] = int((datetime.now(timezone.utc) - start_time).total_seconds())
    args["interval"] = str(args["interval"]) + 's'
    templ = Template(template)
    try:
        result = templ.substitute(**args), None
        return result

    except KeyError:
        logger.debug("Error while attemping to substitute tag in query template")
        return "", "Error while attemping to substitute tag in query template"

def unmarshal(response, provider):
    """
    Unmarshal value from metric response
    """
    logger.info(config.unmarshal)
    if provider not in config.unmarshal.keys():
        logger.error("metrics provider %s not  present in unmarshal object", provider)
        return None, ValueError(f"metrics provider {provider} not present in unmarshal object")
    try:
        num = jq.compile(config.unmarshal[provider]).input(response).first()
        if isinstance(num, numbers.Number) and not np.isnan(num):
            return num, None
        return None, ValueError("Metrics response did not yield a number")
    except Exception as err:
        return None, err

def get_metric_value(metric_resource: MetricResource, version: VersionDetail, start_time: datetime):
    """
    Extrapolate metrics backend URL and query parameters; query the metrics backend;
    and return the value of the metric.
    """
    (value, err) = (None, None)
    url_template = get_metrics_url_template(metric_resource)
    # the following extrapolation is wrong; it should  happen based on secrets
    # url, err = extrapolate(url_template, version, start_time)
    url = url_template
    if err is None:
        params = {}
        for pattern in metric_resource.spec.params:
            pt_key, pt_value = pattern.name, pattern.value
            params[pt_key], err = extrapolate(pt_value, version, start_time)
            if err is not None:
                break
        if err is None:
            # continuing the above example...
            # params now: {"query": "your prometheus query"}
            try:
                logger.debug("Invoking requests get with url %s and params: %s", \
                    url, params)
                response = requests.get(url, params=params, timeout=2.0).json()
            except requests.exceptions.RequestException as exp:
                logger.error("Error while attempting to connect to metrics backend")
                return value, exp
            logger.debug("unmarshaling metrics response...")
            value, err = unmarshal(response, metric_resource.spec.provider)
    return value, err

def get_aggregated_metrics(expr: ExperimentResource):
    """
    Get aggregated metrics from experiment resource and metric resources.
    """
    versions = [expr.spec.versionInfo.baseline]
    if expr.spec.versionInfo.candidates is not None:
        versions += expr.spec.versionInfo.candidates

    messages = []

    iam = AggregatedMetricsAnalysis(data = {})

    #check if start time is greater than now
    if expr.status.startTime > (datetime.now(timezone.utc)):
        messages.append(Message(MessageLevel.error, "Invalid startTime: greater than current time"))
        iam.message = Message.join_messages(messages)
        return iam

    for metric_resource in expr.spec.metrics:
        iam.data[metric_resource.name] = AggregatedMetric(data = {})
        for version in versions:
            iam.data[metric_resource.name].data[version.name] = VersionMetric()
            val, err = get_metric_value(metric_resource.metricObj, version, \
            expr.status.startTime)
            if err is None:
                iam.data[metric_resource.name].data[version.name].value = val
            else:
                messages.append(Message(MessageLevel.error, \
                    f"Error from metrics backend for metric: {metric_resource.name} \
                        and version: {version.name}"))

    iam.message = Message.join_messages(messages)
    logger.debug("Analysis object after metrics collection")
    logger.debug(pprint.PrettyPrinter().pformat(iam))
    return iam
