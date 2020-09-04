"""Module containing classes and methods for querying prometheus and returning metric data.
"""

# core python dependencies
from datetime import datetime, timezone
import logging
from string import Template
import math

# external module dependencies
import requests
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException

# iter8 dependencies
from iter8_analytics.api.analytics.types import RatioMaxMin, \
    CounterDataPoint, CounterQuerySpec, \
    StatusEnum, RatioDataPoint, RatioQuerySpec
import iter8_analytics.constants as constants
from iter8_analytics.config import env_config

logger = logging.getLogger('iter8_analytics')

def new_ratio_max_min(metric_id_to_list_of_values):
    """Return min and max for each ratio metric

    Args:
        metric_id_to_list_of_values (Dict[iter8d, Iterable[float]]):
        dictionary whose keys are metric ids and whose values are a
        list of values seen for each metric

    Returns:
        max_min_lists (Dict[iter8id, RatioMaxMin): dictionary whose keys are
        metric ids and whose values are an object for each metric
        containing its min and max
    """
    max_min_lists = {
        metric_id: [None, None] for metric_id in metric_id_to_list_of_values
    }

    for metric_id in metric_id_to_list_of_values:
        try:
            max_min_lists[metric_id][0], max_min_lists[metric_id][1] = \
                min(metric_id_to_list_of_values[metric_id]), \
                    max(metric_id_to_list_of_values[metric_id])
        except ValueError:
            logger.debug("Empty list of values found for metric %s", metric_id)

        max_min_lists[metric_id] = RatioMaxMin(
                minimum = max_min_lists[metric_id][0],
                maximum = max_min_lists[metric_id][1]
        )
        # if the list of values is empty for a metric id, return None values for max and min

    return max_min_lists

def get_counter_metrics(
    counter_metric_specs, \
    versions, \
    start_time):
    """Query prometheus and get counter metric data for given set of counter metrics and versions.

    Args:
        counter_metric_specs (Dict[iter8id, CounterMetricSpec]):
        dictionary whose values are the counter metric specs and
        whose keys are counter metric ids.
        versions (Iterable[Version]): A iterable of version objects.
        start_time (datetime): start time which dictates
        the duration parameter used in the query.

    Returns:
        Dict[iter8id,  Dict[iter8id, CounterDataPoint]]:
        dictionary whose keys are version ids and whose values are dictionaries.
        The inner dictionary has keys which are metric ids and values
        which are current counter data point values. For e.g.:
        {
            "version1": {
                "metric1": CounterDataPoint(...),
                "metric2": CounterDataPoint(...)
            },
            "version2": {
                "metric1": CounterDataPoint(...),
                "metric2": CounterDataPoint(...)
            }
        }
    """
    cmd = {version.id: {} for version in versions} #  initialize cmd
    # populate cmd
    for counter_metric_spec in counter_metric_specs.values():
        query_spec = CounterQuerySpec(
            version_label_keys = versions[0].version_labels.keys(),
            query_template = counter_metric_spec.query_template,
            start_time = start_time
        )
        pcmq = PrometheusCounterMetricQuery(query_spec, versions)
        current_time = datetime.now(timezone.utc)
        cmd_from_prom = pcmq.query_from_spec(current_time)
        status = StatusEnum.zeroed_counter if cmd_from_prom \
            else StatusEnum.no_versions_in_prom_response
        for version in versions:
            if version.id in cmd_from_prom:
                cmd[version.id][counter_metric_spec.id] = cmd_from_prom[version.id]
            else:
                cmd[version.id][counter_metric_spec.id] = CounterDataPoint(
                    value = 0,
                    timestamp = current_time,
                    status = status
                )
        # if a version cannot be found in the list of counter metrics
        # returned by prometheus, then the value of the counter is assumed
        # to be zero

    return cmd

def get_ratio_metrics(
    ratio_metric_specs, \
    counter_metric_specs, \
    counter_metrics, \
    versions, \
    start_time):
    """Query prometheus and get ratio metric data for given set of ratio metrics and versions.

    Args:
        ratio_metric_specs (Dict[iter8id, RatioMetricSpec]):
        dictionary whose values are the ratio metric specs and
        whose keys are ratio metric ids
        counter_metric_specs (Dict[iter8id, CounterMetricSpec]):
        dictionary whose values are the counter metric specs and
        whose keys are counter metric ids.
        counter_metrics (Dict[iter8id,  Dict[iter8id, CounterDataPoint]]):
        dictionary whose keys are version ids and whose values are dictionaries.
        The inner dictionary has keys which are  metric ids and values which are
        current counter data point values. Typically, the object returned by
        get_counter_metrics(...) method will be used as the value of this argument.
        versions (Iterable[Version]): A iterable of version objects.
        start_time (datetime): start time which dictates the
        duration parameter used in the query.

    Returns:
        Dict[iter8id,  Dict[iter8id, RatioDataPoint]]:
        dictionary whose keys are version ids and whose values are dictionaries.
        The inner dictionary has keys which are metric ids and values which are
        current ratio data point values. For e.g.:
        {
            "version1": {
                "metric1": RatioDataPoint(...),
                "metric2": RatioDataPoint(...)
            },
            "version2": {
                "metric1": RatioDataPoint(...),
                "metric2": RatioDataPoint(...)
            }
        }
    """
    # initialize rmd
    rmd = {version.id: {} for version in versions}

    # populate rmd
    for ratio_metric_spec in ratio_metric_specs.values():
        query_spec = RatioQuerySpec(
            version_label_keys = versions[0].version_labels.keys(),
            numerator_template = \
                counter_metric_specs[ratio_metric_spec.numerator].query_template,
            denominator_template = \
                counter_metric_specs[ratio_metric_spec.denominator].query_template,
            start_time = start_time
        )
        prmq = PrometheusRatioMetricQuery(query_spec, versions)
        current_time = datetime.now(timezone.utc)
        rmd_from_prom = prmq.query_from_spec(current_time)

        for version in versions:
            if version.id in rmd_from_prom:
                rmd[version.id][ratio_metric_spec.id] = rmd_from_prom[version.id]
            else:
                if version.id in counter_metrics and \
                    counter_metrics[version.id][ratio_metric_spec.denominator].value:
                    rmd[version.id][ratio_metric_spec.id] = RatioDataPoint(
                        value = 0,
                        timestamp = current_time,
                        status = StatusEnum.zeroed_ratio
                    )
                else:
                    rmd[version.id][ratio_metric_spec.id] = RatioDataPoint(
                        value = None,
                        timestamp = current_time,
                        status = StatusEnum.absent_version_in_prom_response
                    )
        # if a version cannot be found in the list of ratio metrics
        # returned by prometheus, then the value of the ratio is set to zero
        # if denominator is non-zero, and is set to None otherwise.

    return rmd

class PrometheusMetricQuery():
    """Base class for querying prometheus.

    Attributes:
        prometheus_url (str): Prom url for quering
        query_spec (QuerySpec): Query spec for prom query
        version_labels_to_id (Dict[Set[Tuple[str, str]], str]):
        Dictionary mapping version labels to their ids
    """
    def __init__(self, query_spec, versions):
        """Initialize prometheus metric query object.

        Args:
            query_spec (QuerySpec): Prom query spec
            versions (Iterable[Version]): Iterable of Version objects.
        """
        prometheus_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
        self.prometheus_url = prometheus_url + "/api/v1/query"
        self.query_spec = query_spec
        self.authentication = {
            constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: \
                constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE
        }
        if constants.METRICS_BACKEND_CONFIG_AUTH in env_config:
            self.authentication = env_config[constants.METRICS_BACKEND_CONFIG_AUTH]
        self.version_labels_to_id = {
            frozenset(version.version_labels.items()): version.id for version in versions
        }
        self.versions = versions
        """the above frozenset maps from version labels to version ids
        """

    def query_from_spec(self, current_time):
        """Query prometheus using query spec.

        Args:
            current_time (datetime): Current time needed to compute duration value within the query.

        Returns:
            query_result (Dict[str, Dict[str, DataPoint]]]): Post processed query result
        """
        interval = int((current_time - self.query_spec.start_time).total_seconds())
        if interval < 20.0: # less than twenty seconds has elapsed since start of the experiment
            logger.debug("Less than 20 seconds have elapsed since the start of the experiment")
            return self.post_process({
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": []
                }
            }, current_time)

        kwargs = {
            "interval": f"{interval}s",
            "version_labels": ",".join(self.query_spec.version_label_keys) # also hard coded
        }
        query = self.get_query(kwargs)
        return self.query(query, current_time)

    def get_query(self, query_args):
        """
        Convert query components into a prometheus query
        """
        raise NotImplementedError

    def query(self, query, current_time):
        """Query prometheus using query parameters.

        Args:
            current_time (datetime): Current time needed to compute duration value within the query.

        Returns:
            query_result (Dict[str, Dict[str, DataPoint]]]): Post processed query result

        Raises:
            Exception: HTTP connection errors related to prom requests.
        """
        params = {'query': query}
        auth_type = self.authentication.get(constants.METRICS_BACKEND_CONFIG_AUTH_TYPE)
        logger.debug("authentication type is: %s", auth_type)
        try:
            query_result = None
            if auth_type == constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE:
                query_result = requests.get(self.prometheus_url, params=params).json()
            elif auth_type == constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC:
                auth=HTTPBasicAuth(
                    self.authentication.get(constants.METRICS_BACKEND_CONFIG_AUTH_USERNAME),
                    self.authentication.get(constants.METRICS_BACKEND_CONFIG_AUTH_PASSWORD)
                )
                verify = (not self.authentication.get(\
                    constants.METRICS_BACKEND_CONFIG_AUTH_INSECURE_SKIP_VERIFY))
                query_result = requests.get(self.prometheus_url, params=params, \
                    auth=auth, verify=verify).json()
            else:
                logger.warning("Unsupported authentication type: %s; trying %s",
                    auth_type, constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE)
                query_result = requests.get(self.prometheus_url, params=params).json()
            logger.debug("query result -- raw")
            logger.debug(query_result)
        except Exception as exp:
            logger.error("Error while attempting to connect to prometheus")
            raise HTTPException(status_code=422, \
                detail="Error while attempting to connect to prometheus.") from exp
        return self.post_process(query_result, current_time)

    def post_process(self, raw_query_result, time_stamp):
        """Post process prom query result

        Args:
            raw_query_result ({
                "data": {
                    "result": {
                        "value": [float], # sequence whose element index 1 is the metric value
                        "metric": Dict[str, str] # version labels
                    }
                }
            }): Raw prometheus result
            time_stamp (datetime): time stamp at which prom query was made

        Returns:
            query_result (Dict[str, Dict[str, DataPoint]]]): Post processed query result

        Raises:
            HTTPException: If query was unsuccessful for reasons
            such as 1) bad template, 2) prom result contained no data, or
            3) returned data in a non-vector form which cannot be post processed.
        """
        prom_result = {}
        if raw_query_result["status"] != "success":
            raise HTTPException(status_code=422, \
                detail="Query did not succeed. Check your query template.")
        if "data" not in raw_query_result:
            return HTTPException(status_code=422, \
                detail="Query did not succeed. Prometheus returned without data.")
        if raw_query_result["data"]['resultType'] != 'vector':
            return HTTPException(status_code=422, \
                detail="Query succeeded but returned with a non-vector result. \
                    Check your query template.")
        # query succeeded and we have some proper data to work with
        results = raw_query_result["data"]["result"]
        for result in results:
            version_ids = self.get_version_ids(result['metric'])
            for version_id in version_ids:
                prom_result[version_id] = \
                    self.result_value_to_data_point(result['value'][1], time_stamp)

        return prom_result

    def result_value_to_data_point(self, result_value, time_stamp):
        """
        Convert result value to counter or ratio data point
        """
        raise NotImplementedError

    def get_version_id(self, version_labels):
        """Get version id from version labels.

        Args:
            version_labels (Dict[str, str]): Dictionary of labels and their values for a version

        Returns:
            version_id (str): id of the corresponding version
        """
        return self.version_labels_to_id.get(frozenset(version_labels.items()), None)

    def get_version_ids(self, version_labels):
        """Get version ids from version labels.

        Args:
            version_labels (Dict[str, str]): Dictionary of labels and their values for a version

        Returns:
            version_ids (str): ids of versions with matching version labels
        """
        return [version.id for version in self.versions if \
            frozenset(version_labels.items()) == version.version_labels.items()]


class PrometheusCounterMetricQuery(PrometheusMetricQuery):
    """Derived class for querying prometheus for counter metric.
    """
    def get_query(self, query_args):
        """Extrapolate query from counter query spec and query_args

        Args:
            query_args (Dict[str, str]):
            Dictionary of values of template variables in counter query spec

        Returns:
            query (str): The query string used for querying prom
        """

        query_template = Template(self.query_spec.query_template)
        query = query_template.substitute(**query_args)
        logger.debug("Query: %s", query)
        return query

    def result_value_to_data_point(self, result_value, time_stamp):
        """Convert prometheus result value in string format to CounterDataPoint

        Args:
            result_value (str): Raw prometheus result value
            ts (datetime): time stamp at which prom query was made

        Returns:
            counter_data_point (CounterDataPoint): Counter data point
        """

        result_float = float(result_value)
        assert not math.isnan(result_float)
        return CounterDataPoint(
            value = result_float,
            timestamp = time_stamp)
        # Counter data point can never have a None value

class PrometheusRatioMetricQuery(PrometheusMetricQuery):
    """Derived class for querying prometheus for counter metric.
    """
    def get_query(self, query_args):
        """Extrapolate query from ratio query spec and query_args

        Args:
            query_args (Dict[str, str]): Dictionary of values of template variables in query_spec

        Returns:
            query (str): The query string used for querying prom
        """
        num_query_template = Template(self.query_spec.numerator_template)
        num_query = num_query_template.substitute(**query_args)
        den_query_template = Template(self.query_spec.denominator_template)
        den_query = den_query_template.substitute(**query_args)
        query = f"({num_query}) / ({den_query})"
        logger.debug("Query: %s", query)
        return query

    def result_value_to_data_point(self, result_value, time_stamp):
        """Convert prometheus result value in string format to RatioDataPoint

        Args:
            result_value (str): Raw prometheus result value
            ts (datetime): time stamp at which prom query was made

        Returns:
            ratio_data_point (RatioDataPoint): Ratio data point
        """

        result_float = float(result_value)
        return RatioDataPoint(
            value = None,
            timestamp = time_stamp,
            status = StatusEnum.nan_value
        ) if math.isnan(result_float) or math.isinf(result_float) else RatioDataPoint(
            value = result_float,
            timestamp = time_stamp
        )
