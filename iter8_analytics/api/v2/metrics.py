"""
Module containing classes and methods for querying prometheus and returning metric data.
"""
# core python dependencies
from datetime import datetime, timezone
import logging
from string import Template
from typing import Sequence, Dict, Any
import numbers
import pprint
import base64
import binascii
import json

# external module dependencies
import requests
from requests.auth import HTTPBasicAuth
import numpy as np
import jq
from cachetools import cached, TTLCache
from kubernetes import client as kubeclient
from kubernetes import config as kubeconfig

# iter8 dependencies
from iter8_analytics.api.v2.types import AggregatedMetricsAnalysis, ExperimentResource, \
    MetricResource, VersionDetail, AggregatedMetric, VersionMetric, MetricType, \
    AuthType, Method
from iter8_analytics.api.utils import Message, MessageLevel

logger = logging.getLogger('iter8_analytics')

# namespaced names of builtin metrics
builtin_metrics_nn = [
    "iter8-system/request-count",
    "iter8-system/error-count",
    "iter8-system/error-rate",
    "iter8-system/mean-latency",
    "iter8-system/latency-50th-percentile", # median
    "iter8-system/latency-75th-percentile",
    "iter8-system/latency-90th-percentile",
    "iter8-system/latency-95th-percentile",
    "iter8-system/latency-99th-percentile"
]

# cache secrets data for no longer than ten seconds
@cached(cache=TTLCache(maxsize=1024, ttl=10))
def get_secret_data(name, namespace):
    """fetch a secret from Kubernetes cluster and return its decoded data"""
    # use in-cluster kubernetes client to fetch secret
    kubeconfig.load_incluster_config()
    core = kubeclient.CoreV1Api()
    try:
        sec = core.read_namespaced_secret(name, namespace)
    except kubeclient.exceptions.ApiException as exc:
        logger.error("An exception occurred while attempting to read secret.. \
            does iter8-analytics have RBAC permissions for reading this secret?")
        return None, exc
    # at this point, the read_namespaced_secret call succeeded...
    if sec is None:
        return None, KeyError(f"cannot find secret {name} in namespace {namespace}")
    # there is a secret in the namespace...
    sec_data = {}
    # data is an optional field in k8s secrets...
    if sec.data is not None:
        for field in sec.data:
            try:
                # ascii decoding of data is the lowest common denominator
                # HTTP headers need to be ascii encoded
                sec_data[field] = base64.b64decode(sec.data[field]).decode(encoding="ascii")
            except (UnicodeDecodeError, binascii.Error) as err:
                return None, err
    return sec_data, None

def get_secret_data_for_metric(metric_resource: MetricResource):
    """fetch a secret referenced in a metric from Kubernetes cluster and return its decoded data"""
    # python k8s client does not have a clean call finding current namespace...
    # this is the most accepted answer at this point
    my_ns = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
    if metric_resource.spec.secret is None:
        return None, ValueError("metric does not reference any secret")
    # there is a secret referenced in the metric ...
    namespaced_name = metric_resource.spec.secret.split("/")
    if len(namespaced_name) == 1: # secret does not have a namespace in it
        args, err = get_secret_data(namespaced_name[0], my_ns)
    elif len(namespaced_name) == 2: # secret has a namespace in it
        args, err = get_secret_data(namespaced_name[1], namespaced_name[0])
    return args, err

def interpolate(template: str, args: dict):
    """
    Interpolate a template string using a dictionary
    """
    if args is None:
        return template, None
    try:
        templ = Template(template)
        # if placeholder values are not present in args dictionary,
        # then no interpolation will occur ... this is the behavior of safe_substitute
        result = templ.safe_substitute(**args), None
        return result
    except Exception:
        logger.error("Error while attemping to substitute tag in query template")
        return None, "Error while attemping to substitute tag in query template"

def get_url(metric_resource: MetricResource):
    """Derive URL by substituting placeholders in the URLTemplate of a metric resource.
    Placeholder substitution will be attempted if the metric resource references a valid secret.

    Keyword arguments:
    metric_resource: the metric resource
    """
    if metric_resource.spec.urlTemplate is None:
        return None, ValueError("No URL template is available in metric resource")
    if metric_resource.spec.secret is None: # no need to interpolate
        return metric_resource.spec.urlTemplate, None
    args, err = get_secret_data_for_metric(metric_resource)
    # interpolate urlTemplate string using secret data
    if err is None:
        return interpolate(metric_resource.spec.urlTemplate, args)
    return None, err

def get_headers(metric_resource: MetricResource):
    """
    Get the headers to be used in the REST query for the given metric.
    """
    headers = {}
    # no headers will be used
    if metric_resource.spec.headerTemplates is None:
        return headers, None
    # initialize headers dictionary
    for item in metric_resource.spec.headerTemplates:
        headers[item.name] = item.value
    # if authType is None, interpolation is not attempted
    if metric_resource.spec.authType is None:
        return headers, None
    # if authType is Basic, interpolation is not attempted
    if metric_resource.spec.authType == AuthType.BASIC:
        return headers, None
    # if there is no secret referenced, interpolation is not attempted
    if metric_resource.spec.secret is None:
        return headers, None

    # args contain decoded secret data for header template interpolation
    args, err = get_secret_data_for_metric(metric_resource)
    if err is None:
        for key in headers:
            headers[key], err = interpolate(headers[key], args)
            if err is not None:
                return None, err
        return headers, None
    return None, err

def get_basic_auth(metric_resource: MetricResource):
    """
    Get basic auth information.
    """
    # return error if authType is not Basic
    if metric_resource.spec.authType is None or \
        metric_resource.spec.authType != AuthType.BASIC:
        return None, \
            ValueError("get_basic_auth call is not supported for None/non-Basic auth types")

    # return error if secret is missing
    if metric_resource.spec.secret is None:
        return None, ValueError("basic auth requires a secret")

    # args contain decoded secret data for basic auth
    args, err = get_secret_data_for_metric(metric_resource)
    if err is None:
        if "username" in args and "password" in args:
            return HTTPBasicAuth(args["username"], args["password"]), None
        return None, ValueError("username and password keys missing in secret data")
    return None, err

def get_elapsed_time_seconds(start_time) -> int:
    """
    If start time is in the future, make it 1 second
    """
    elapsed = int((datetime.now(timezone.utc) - start_time).total_seconds())
    return max(elapsed, 1) # at least one second

def get_params(metric_resource: MetricResource, version: VersionDetail, start_time: datetime):
    """Interpolate REST query params for metric and return interpolated params"""
    # args contain data from VersionInfo,
    # along with elapsedTime (time since the start of experiment)
    args = {}
    args["name"] = version.name
    if version.variables is not None and len(version.variables) > 0:
        for variable in version.variables:
            args[variable.name] = variable.value
    elapsed = get_elapsed_time_seconds(start_time)
    args["elapsedTime"] = str(elapsed)

    params = {}
    if  metric_resource.spec.params is not None:
        for par in metric_resource.spec.params:
            params[par.name], err = interpolate(par.value, args)
            if err is not None:
                return None, err
    return params, None

def get_body(metric_resource: MetricResource, version: VersionDetail, start_time: datetime):
    """Interpolate POST query body for metric and return interpolated body"""
    # args contain data from VersionInfo,
    # along with elapsedTime (time since the start of experiment)
    args = {}
    args["name"] = version.name
    if version.variables is not None and len(version.variables) > 0:
        for variable in version.variables:
            args[variable.name] = variable.value
    elapsed = get_elapsed_time_seconds(start_time)
    args["elapsedTime"] = str(elapsed)

    if metric_resource.spec.body is None:
        return None, None

    interpolated_body, err = interpolate(metric_resource.spec.body, args)
    if err is not None:
        return None, err

    try:
        body = json.loads(interpolated_body)
        return body, None
    except json.JSONDecodeError as jde:
        return None, jde

def get_raw_response(url, method, params, body, headers, auth, timeout):
    """Send GET or POST request to the url and get HTTP response"""
    kw_args = {
        "url": url,
        "verify": False,
    }

    if params is not None:
        kw_args["params"] = params
    if headers is not None:
        kw_args["headers"] = headers
    if body is not None:
        kw_args["json"] = body
    if auth is not None:
        kw_args["auth"] = auth
    if timeout is not None:
        kw_args["timeout"] = timeout

    if method == Method.GET:
        return requests.get(**kw_args)
    if method == Method.POST:
        return requests.post(**kw_args)
    raise ValueError("Unknown HTTP request method")

def unmarshal(response, jq_expression):
    """
    Unmarshal metric value from metric response
    """
    try:
        # in general, jq execution could yield multiple values
        # we will use the first value
        num = jq.compile(jq_expression).input(response).first()
        # if that value is not a number, there is an error
        if isinstance(num, numbers.Number) and not np.isnan(num):
            return num, None
        return None, ValueError("Metrics response did not yield a number")
    except Exception as err:
        return None, err

def is_mocked(metric_resource: MetricResource) -> bool:
    """
    Is this metrics a mocked metric or a real metric?
    """
    return metric_resource.spec.mock is not None

def mocked_value(metric_resource: MetricResource, version: VersionDetail, start_time: datetime)\
    -> (numbers.Number, BaseException):
    """
    Return a mock value for a mocked metric.
    """
    # if no level is available for version, return error
    named_level = None

    for nal in metric_resource.spec.mock:
        if nal.name == version.name:
            named_level = nal
            break

    if named_level is None:
        return None, ValueError("metrics does not specify how to mock value for version")

    # metric does specify how to mock value for version
    # compute time elapsed
    elapsed = get_elapsed_time_seconds(start_time)
    # the logic for mocked values is below...
    # https://github.com/iter8-tools/etc3/blob/\
    # 1f747f07de7008895717c415dac9173b57374afa/api/v2alpha2/metric_types.go#L71
    if metric_resource.spec.type == MetricType.Counter:
        return (elapsed * named_level.level, None)
    else: # gauge metric
        _alpha = elapsed
        _beta = elapsed
        beta = np.random.beta(_alpha, _beta)
        return (beta * 2 * named_level.level, None)

def get_metric_value(metric_resource: MetricResource, version: VersionDetail, start_time: datetime):
    """
    Interpolate metrics backend URL, headerTemplates, and REST query parameters;
    query the metrics backend; return the value of the metric.
    """
    if is_mocked(metric_resource):
        metric_resource.spec.convert_to_float()
        return mocked_value(metric_resource, version, start_time)

    (value, err) = (None, None)
    # interpolated metrics backend URL
    url, err = get_url(metric_resource)
    params, headers, auth, body = None, None, None, None
    if err is None:
        # interpolated params
        params, err = get_params(metric_resource, version, start_time)
        logger.debug("Params error: %s", err)
        if params == {}:
            params = None
    if err is None:
        # interpolated header templates
        headers, err = get_headers(metric_resource)
        logger.debug("Headers error: %s", err)
        if headers == {}:
            headers = None
    if err is None:
        if metric_resource.spec.authType == AuthType.BASIC:
            # basic auth info
            auth, err = get_basic_auth(metric_resource)
            logger.debug("Auth error: %s", err)
    if err is None:
        body, err = get_body(metric_resource, version, start_time)
        logger.debug("Body error: %s", err)

    if err is None:
        try:
            logger.debug("Invoking requests with method %s and with \
                url %s and params: %s and headers: %s and auth: %s and body: %s", \
                    metric_resource.spec.method, url, params, headers, auth, body)
            raw_response = get_raw_response(url = url, \
                method = metric_resource.spec.method, params = params, body = body, \
                    headers = headers, auth = auth, timeout = 5.0)
            logger.debug("response status code: %s", raw_response.status_code)
            logger.debug("response text: %s", raw_response.text)
            response = raw_response.json()
            logger.debug("json response...")
            logger.debug(response)
        except (requests.exceptions.RequestException, \
            json.decoder.JSONDecodeError, ValueError) as exc:
            logger.error("Error while attempting to get metric value from backend")
            logger.error(exc)
            return value, exc
        logger.debug("unmarshaling metrics response using jqExpression...")
        if metric_resource.spec.jqExpression is None:
            return value, ValueError("no jqExpression is specific in metric resource")
        value, err = unmarshal(response, metric_resource.spec.jqExpression)
    return value, err

# We will mirror the following handler data structures below...

# // DurationSample is a Fortio duration sample
# type DurationSample struct {
# 	Start float64
# 	End   float64
# 	Count int
# }

# // DurationHist is the Fortio duration histogram
# type DurationHist struct {
# 	Count int
# 	Max   float64
# 	Sum   float64
# 	Data  []DurationSample
# }

# // Result is the result of a single Fortio run; it contains the result for a single version
# type Result struct {
# 	DurationHistogram DurationHist
# 	RetCodes          map[string]int
# }

class DurationSample:
    """
    DurationSample is a Fortio duration sample.
    """
    def __init__(self, sample: Dict[str, Any]):
        self.start: float = float(sample["Start"])
        self.end: float = float(sample["End"])
        self.count: int = int(sample["Count"])

class DurationHist:
    """
    DurationHist is a Fortio duration histogram.
    """
    def __init__(self, dur_hist: Dict[str, Any]):
        self.count: int = int(dur_hist["Count"])
        self.max: float = float(dur_hist["Max"])
        self.sum: float = float(dur_hist["Sum"])
        self.data: Sequence[DurationSample] = [
            DurationSample(sample) for sample in dur_hist["Data"]
        ]

class Result:
    """
    Result is the result of a single Fortio run; it contains the result for a single version
    """
    def __init__(self, result: Dict[str, Any]):
        self.duration_histogram: DurationHist = DurationHist(result["DurationHistogram"])
        self.ret_codes: Dict[str, int] = {
            key: int(value) for (key, value) in result["RetCodes"].items()
        }

class Builtins:
    """
    Builtins contains results for all versions
    """
    def __init__(self, data: Dict[str, Any]):
        self.version_results: Dict[str, Result] = {
            key: Result(value) for (key, value) in data.items()
        }

def initialize_builtins(iam: AggregatedMetricsAnalysis):
    """
    Initialize builtin metrics in iam
    """
    for metric_nn in builtin_metrics_nn:
        iam.data[metric_nn] = AggregatedMetric(data = {})

def populate_builtins_for_version(iam: AggregatedMetricsAnalysis, \
    version_name: str, result: Result):
    """
    Populate builtin metrics in iam for version
    1. Latency values will be converted to milliseconds
    2. Random seed will be fixed to ensure repeatability
    """
    # initialize random state for numpy
    np.random.seed(17) # actual number... 17 in this case... is not important

    # populate request count
    iam.data["iter8-system/request-count"].data[version_name] = VersionMetric(
        value = result.duration_histogram.count
    )

    # populate error count
    error_count: int = 0
    for (key, val) in result.ret_codes.items():
        if int(key) >= 400:
            error_count += val
    iam.data["iter8-system/error-count"].data[version_name] = VersionMetric(
        value = error_count
    )

    # populate error rate
    if result.duration_histogram.count > 0:
        iam.data["iter8-system/error-rate"].data[version_name] = VersionMetric()
        iam.data["iter8-system/error-rate"].data[version_name].value = \
            float(iam.data["iter8-system/error-count"].data[version_name].value) \
                / float(iam.data["iter8-system/request-count"].data[version_name].value)

    # populate mean latency (in msec)
    if result.duration_histogram.count > 0:
        iam.data["iter8-system/mean-latency"].data[version_name] = VersionMetric()
        iam.data["iter8-system/mean-latency"].data[version_name].value = \
            1000.0 * float(result.duration_histogram.sum) \
                / float(result.duration_histogram.count)

    # populate tail latencies
    if result.duration_histogram.count > 0:
        # create sample of size 1000+
        sample = np.array([])
        for duras in result.duration_histogram.data:
            if duras.count > 0:
                # 10x random sample
                npr = np.random.uniform(1000.0 * duras.start, 1000.0 * duras.end, 10*duras.count)
                sample = np.concatenate((sample, npr), axis = None)
        # if sample is not-empty
        # compute and populate tail latencies
        if sample.size > 0:
            tail50 = np.percentile(sample, 50)
            tail75 = np.percentile(sample, 75)
            tail90 = np.percentile(sample, 90)
            tail95 = np.percentile(sample, 95)
            tail99 = np.percentile(sample, 99)
            iam.data["iter8-system/latency-50th-percentile"].data[version_name] = VersionMetric()
            iam.data["iter8-system/latency-50th-percentile"].data[version_name].value = tail50
            iam.data["iter8-system/latency-75th-percentile"].data[version_name] = VersionMetric()
            iam.data["iter8-system/latency-75th-percentile"].data[version_name].value = tail75
            iam.data["iter8-system/latency-90th-percentile"].data[version_name] = VersionMetric()
            iam.data["iter8-system/latency-90th-percentile"].data[version_name].value = tail90
            iam.data["iter8-system/latency-95th-percentile"].data[version_name] = VersionMetric()
            iam.data["iter8-system/latency-95th-percentile"].data[version_name].value = tail95
            iam.data["iter8-system/latency-99th-percentile"].data[version_name] = VersionMetric()
            iam.data["iter8-system/latency-99th-percentile"].data[version_name].value = tail99

def get_builtin_metrics(expr: ExperimentResource):
    """
    Get built in metrics using experiment resource.
    """
    # initialize aggregated metrics object
    iam = AggregatedMetricsAnalysis(data = {})
    if expr.status.analysis is None or \
        expr.status.analysis.aggregated_builtin_hists is None:
        return iam
    builtins = Builtins(expr.status.analysis.aggregated_builtin_hists["data"])
    initialize_builtins(iam)
    for version in builtins.version_results:
        populate_builtins_for_version(iam, version, builtins.version_results[version])
    return iam

def get_aggregated_metrics(expr: ExperimentResource):
    """
    Get aggregated metrics using experiment resource and metric resources.
    """
    versions = [expr.spec.versionInfo.baseline]
    if expr.spec.versionInfo.candidates is not None:
        versions += expr.spec.versionInfo.candidates

    # messages not working as intended...
    messages = []

    # initialize aggregated metrics object
    iam = get_builtin_metrics(expr)

    # there are no metrics to be fetched
    if expr.status.metrics is None:
        iam.message = Message.join_messages(messages)
        return iam

    for metric_info in expr.status.metrics:
        # only custom metrics is handled below... not builtin metrics
        if metric_info.metricObj.spec.provider is None or \
            metric_info.metricObj.spec.provider != "iter8":
            iam.data[metric_info.name] = AggregatedMetric(data = {})
            # fetch the metric value for each version...
            for version in versions:
                # initialize metric object for this version...
                iam.data[metric_info.name].data[version.name] = VersionMetric()
                val, err = get_metric_value(metric_info.metricObj, version, \
                expr.status.startTime)
                if err is None and val is not None:
                    iam.data[metric_info.name].data[version.name].value = val
                else:
                    try:
                        val = float(expr.status.analysis.aggregated_metrics.data\
                            [metric_info.name].data[version.name].value)
                    except AttributeError:
                        val = None
                    iam.data[metric_info.name].data[version.name].value = val
                if err is not None:
                    messages.append(Message(MessageLevel.ERROR, \
                        f"Error from metrics backend for metric: {metric_info.name} \
                            and version: {version.name}"))

    iam.message = Message.join_messages(messages)
    logger.debug("Analysis object after metrics collection")
    logger.debug(pprint.PrettyPrinter().pformat(iam))
    return iam
