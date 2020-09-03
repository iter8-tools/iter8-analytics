# core python dependencies
import logging
import os
import sys
import yaml

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

import iter8_analytics.constants as constants

# def get_env_config():
#     """
# Read the environment variables that control the server behavior and
# populate the config dictionary

#       Returns:
#         config (Dict): config dictionary
#       """

#     prom_url = os.getenv(constants.METRICS_BACKEND_URL_ENV)
#     if prom_url is None:
#         logging.getLogger('iter8_analytics').critical(
#             u'The environment variable {0} was not set. '
#             'Example of a valid value: "http://localhost:9090". '
#             'Aborting!'.format(constants.METRICS_BACKEND_URL_ENV))
#         sys.exit(1)

#     val = URLValidator()
#     try:
#         val(prom_url)
#     except ValidationError as e:
#         logging.getLogger('iter8_analytics').critical(f'Prometheus URL {prom_url} is invalid', e)
#         sys.exit(1)

#     logging.getLogger('iter8_analytics').info('Configuring iter8 analytics server')

#     config = {}
#     config[constants.ITER8_ANALYTICS_LOG_LEVEL_ENV] = os.getenv(
#         constants.ITER8_ANALYTICS_LOG_LEVEL_ENV, 'debug')

#     config[constants.ANALYTICS_SERVICE_PORT] = os.getenv(
#         constants.ANALYTICS_SERVICE_PORT, 5555)

#     logging.getLogger('iter8_analytics').info(
#         u'The iter8 analytics server will listen on port {0}. '
#         'This value can be set by the environment variable {1}'.format(config[constants.ANALYTICS_SERVICE_PORT], constants.ANALYTICS_SERVICE_PORT))

#     return config


def read_config_file():
    configFile = os.getenv(
        constants.METRICS_BACKEND_CONFIGFILE_ENV,
        constants.METRICS_BACKEND_DEFAULT_CONFIGFILE)
    logging.getLogger(__name__).info(f"Reading config file: {configFile}")

    try:
        with open(configFile, 'r') as stream:
            try:
                configYaml = yaml.safe_load(stream)
            except yaml.YAMLError:
                logging.getLogger(__name__).warning(
                    f"Unable to parse configuration file {configFile}; ignoring")
                return {}
    except IOError:
        logging.getLogger(__name__).warning(
            f"Unable to read configuration file {configFile}; ignoring")
        return {}

    # validate metricsBackend config if present
    if constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND in configYaml:
        metricsBackend = configYaml[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND]
        # if backend type is specified, verify that it is in the supported set
        # {prometheus}
        if constants.METRICS_BACKEND_CONFIG_TYPE in metricsBackend:
            if not (metricsBackend[constants.METRICS_BACKEND_CONFIG_TYPE] in [
                    constants.METRICS_BACKEND_CONFIG_TYPE_PROMETHEUS]):
                logging.getLogger(__name__).error(
                    f"Only {constants.METRICS_BACKEND_CONFIG_TYPE_PROMETHEUS} is supported. Ignoring {constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND} configuration.")
        # if auth.type is specified, verify tht it is in the supported set
        # {none, basic}
        if constants.METRICS_BACKEND_CONFIG_AUTH in metricsBackend:
            auth = metricsBackend[constants.METRICS_BACKEND_CONFIG_AUTH]
            if constants.METRICS_BACKEND_CONFIG_AUTH_TYPE in auth:
                if not (auth[constants.METRICS_BACKEND_CONFIG_AUTH_TYPE] in [
                        constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE, constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC]):
                    logging.getLogger(__name__).error(
                        f"Only {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC} (or {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}) authentication supported. Trying {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}")
                    configYaml[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND][constants.METRICS_BACKEND_CONFIG_AUTH][
                        constants.METRICS_BACKEND_CONFIG_AUTH_TYPE] = constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE
    return configYaml


def get_env_config():
    ''' Reads config from config file. Config file default is './config.yaml'
    but can be overwritten by an environment variable METRICS_BACKEND_CONFIGFILE'''
    configMap = read_config_file()
    config = {}

    # log level
    # default value
    config[constants.LOG_LEVEL] = constants.LOG_LEVEL_DEFAULT_LEVEL
    # override with value in configFile
    # TODO
    # override with environment variable
    config[constants.LOG_LEVEL] = os.getenv(
        constants.ITER8_ANALYTICS_LOG_LEVEL_ENV, config[constants.LOG_LEVEL])

    # port
    # default value
    config[constants.ANALYTICS_SERVICE_PORT] = constants.ANALYTICS_SERVICE_DEFAULT_PORT
    logging.getLogger(__name__).info(
        f"Default port is: {config[constants.ANALYTICS_SERVICE_PORT]}")
    # override with value in configFile
    if constants.ANALYTICS_SERVICE_CONFIGFILE_PORT in configMap:
        config[constants.ANALYTICS_SERVICE_PORT] = configMap[constants.ANALYTICS_SERVICE_CONFIGFILE_PORT]
        logging.getLogger(__name__).info(
            f"Port in config file is: {config[constants.ANALYTICS_SERVICE_PORT]}")
    # override with value in env variable
    config[constants.ANALYTICS_SERVICE_PORT] = os.getenv(
        constants.ANALYTICS_SERVICE_PORT_ENV, config[constants.ANALYTICS_SERVICE_PORT])
    # log result
    logging.getLogger(__name__).info(
        f"The iter8 analytics server will listen on port {config[constants.ANALYTICS_SERVICE_PORT]}")

    # metrics backend
    # default value
    config[constants.METRICS_BACKEND_CONFIG_URL] = constants.METRICS_BACKEND_CONFIG_DEFAULT_URL
    logging.getLogger(__name__).info(
        f"Set default url as: {config[constants.METRICS_BACKEND_CONFIG_URL]}")
    config[constants.METRICS_BACKEND_CONFIG_AUTH] = {
        constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE
    }
    logging.getLogger(__name__).info(
        f"Set default auth as: {config[constants.METRICS_BACKEND_CONFIG_AUTH]}")
    # override with value in configFile
    if constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND in configMap:
        backend = configMap[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND]
        if constants.METRICS_BACKEND_CONFIGFILE_URL in backend:
            config[constants.METRICS_BACKEND_CONFIG_URL] = backend[constants.METRICS_BACKEND_CONFIGFILE_URL]
            logging.getLogger(__name__).info(
                f"Set url from config as: {config[constants.METRICS_BACKEND_CONFIG_URL]}")
        if constants.METRICS_BACKEND_CONFIG_AUTH in backend:
            config[constants.METRICS_BACKEND_CONFIG_AUTH].update(
                backend[constants.METRICS_BACKEND_CONFIG_AUTH])
            logging.getLogger(__name__).info(
                f"Merged auth from config as: {config[constants.METRICS_BACKEND_CONFIG_AUTH]}")
    # override with value in environment variable (in which case no )
    if os.getenv(constants.METRICS_BACKEND_URL_ENV):
        config[constants.METRICS_BACKEND_CONFIG_URL] = os.getenv(
            constants.METRICS_BACKEND_URL_ENV)
        logging.getLogger(__name__).info(
            f"Set url from env as: {config[constants.METRICS_BACKEND_CONFIG_URL]}")
    # validate
    val = URLValidator()
    try:
        val(config[constants.METRICS_BACKEND_CONFIG_URL])
    except ValidationError as e:
        logging.getLogger('iter8_analytics').critical(
            f'Prometheus URL {config[constants.METRICS_BACKEND_CONFIG_URL]} is invalid', e)
        sys.exit(1)
    # log result
    logging.getLogger(__name__).info(
        f"The backend metrics server is {config[constants.METRICS_BACKEND_CONFIG_URL]}")

    # debug mode
    # default is False
    # currently only specifiable by environment variable
    debug_mode = os.getenv(constants.ITER8_ANALYTICS_DEBUG_ENV, 'false')
    if debug_mode == '1' or str.lower(debug_mode) == 'true':
        config[constants.ITER8_ANALYTICS_DEBUG_ENV] = True
    else:
        config[constants.ITER8_ANALYTICS_DEBUG_ENV] = False
    # log result
    logging.getLogger(__name__).info(u'Debug mode: {0}'.format(debug_mode))

    return config


env_config = get_env_config()
