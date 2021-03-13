"""
Module containing classes and methods for querying prometheus and returning metric data.
"""
# core python dependencies
from datetime import datetime, timezone
import logging
from string import Template
import numbers
import pprint
import base64
import binascii

# external module dependencies
import requests
import numpy as np
import jq
from cachetools import cached, TTLCache
from kubernetes import client as kubeclient
from kubernetes import config as kubeconfig

# iter8 dependencies
from iter8_analytics.api.v2.types import AggregatedMetricsAnalysis, ExperimentResource, \
    MetricResource, VersionDetail, AggregatedMetric, VersionMetric
import iter8_analytics.config as config
from iter8_analytics.api.utils import Message, MessageLevel

logger = logging.getLogger('iter8_analytics')

# cache secrets data for no longer than ten seconds
@cached(cache=TTLCache(maxsize=1024, ttl=10))
def get_secret_data(name, namespace):
    """fetch a secret from Kubernetes cluster and return its decoded data"""
    kubeconfig.load_kube_config()
    core = kubeclient.CoreV1Api()
    sec = core.read_namespaced_secret(name, namespace)
    if sec is None:
        return None, KeyError(f"cannot find secret {name} in namespace {namespace}")
    sec_data = {}
    if sec.data is not None:
        for field in sec.data:
            try:
                sec_data[field] = base64.b64decode(sec.data[field]).decode(encoding="ascii")
            except (UnicodeDecodeError, binascii.Error) as err:
                return None, err
    return sec_data, None

def get_secret_data_for_metric(metric_resource: MetricResource):
    """fetch a secret referenced in a metric from Kubernetes cluster and return its decoded data"""
    my_ns = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
    if metric_resource.spec.secret is None:
        return None, "metric does not reference any secret"
    namespaced_name = metric_resource.spec.secret.split("/")
    if len(namespaced_name) == 1:
        args, err = get_secret_data(namespaced_name[0], my_ns)
    elif len(namespaced_name) == 2:
        args, err = get_secret_data(namespaced_name[1], namespaced_name[0])
    return args, err

def interpolate(template: str, args: dict):
    """
    Interpolate a template using a dictionary
    """
    templ = Template(template)
    try:
        result = templ.safe_substitute(**args), None
        return result
    except Exception:
        logger.error("Error while attemping to substitute tag in query template")
        return None, "Error while attemping to substitute tag in query template"

def get_url(metric_resource: MetricResource):
    """
    Get the URL template for the given metric.
    """
    if metric_resource.spec.secret is None:
        return metric_resource.spec.urlTemplate, None
    args, err = get_secret_data_for_metric(metric_resource)
    if err is None:
        return interpolate(metric_resource.spec.urlTemplate, args)
    return None, err

def get_headers(metric_resource: MetricResource):
    """
    Get the headers to be used in the REST query for the given metric.
    """
    headers = {}
    if metric_resource.spec.headerTemplates is None:
        return headers, None
    for item in metric_resource.spec.headerTemplates:
        headers[item.name] = item.value
    if metric_resource.spec.secret is None:
        return headers, None

    args, err = get_secret_data_for_metric(metric_resource)
    if err is None:
        for key in headers:
            headers[key], err = interpolate(headers[key], args)
            if err is not None:
                return None, err
        return headers, None
    return None, err

def get_params(metric_resource: MetricResource, version: VersionDetail, start_time: datetime):
    """Interpolate parameter values for metric and return params"""
    args = {}
    args["name"] = version.name
    if version.variables is not None and len(version.variables) > 0:
        for variable in version.variables:
            args[variable.name] = variable.value
    args["interval"] = int((datetime.now(timezone.utc) - start_time).total_seconds())
    args["interval"] = str(args["interval"]) + 's'

    params = {}
    for par in metric_resource.spec.params:
        params[par.name], err = interpolate(par.value, args)
        if err is not None:
            return None, err
    return params, None

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
    # the following extrapolation is wrong; it should  happen based on secrets
    # url, err = extrapolate(url_template, version, start_time)
    url, err = get_url(metric_resource)
    if err is None:
        headers, err = get_headers(metric_resource)
    if err is None:
        params, err = get_params(metric_resource, version, start_time)
    if err is None:
        try:
            logger.debug("Invoking requests get with url %s and params: %s", url, params)
            response = requests.get(url, params = params, headers = headers, timeout = 2.0).json()
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

    if expr.spec.metrics is not None:
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
