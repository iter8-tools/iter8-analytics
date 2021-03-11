"""Provides functions for reading configuration and unmarshal information"""
import logging
import os
import yaml

import iter8_analytics.constants as constants

def get_unmarshal():
    """Get unmarshal map that providers unmarshal logic for all metric backends"""
    unmarshal_file = os.getenv(constants.UNMARSHAL_FILE_ENV)
    if unmarshal_file is None:
        logging.getLogger(__name__).error(\
            "%s environment variable not set", constants.UNMARSHAL_FILE_ENV)
        return {}

    logging.getLogger(__name__).info("reading unmarshal file: %s", unmarshal_file)

    try:
        with open(unmarshal_file, 'r') as stream:
            try:
                _unmarshal = yaml.safe_load(stream)
            except yaml.YAMLError:
                logging.getLogger(__name__).warning(\
                    "unable to parse configuration file %s; ignoring", unmarshal_file)
                return {}
    except IOError:
        logging.getLogger(__name__).warning(\
            "Unable to read configuration file %s; ignoring", unmarshal_file)
        return {}
    return _unmarshal

unmarshal = get_unmarshal()

def get_env_config():
    ''' Reads ITER8 config information for env variables'''
    config = {}

    # log level
    # default value
    config[constants.LOG_LEVEL] = constants.LOG_LEVEL_DEFAULT_LEVEL
    # override with environment variable
    config[constants.LOG_LEVEL] = os.getenv(
        constants.ITER8_ANALYTICS_LOG_LEVEL_ENV, config[constants.LOG_LEVEL])

    # port
    # default value
    config[constants.ANALYTICS_SERVICE_PORT] = constants.ANALYTICS_SERVICE_DEFAULT_PORT
    # override with value in env variable
    config[constants.ANALYTICS_SERVICE_PORT] = os.getenv(
        constants.ANALYTICS_SERVICE_PORT_ENV, config[constants.ANALYTICS_SERVICE_PORT])
    # log result
    logging.getLogger(__name__).info(\
        "The iter8 analytics server will listen on port %s", \
            config[constants.ANALYTICS_SERVICE_PORT])

    return config

env_config = get_env_config()
