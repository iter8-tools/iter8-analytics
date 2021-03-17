"""Provides functions for reading configuration information"""
import logging
import os

import iter8_analytics.constants as constants

def get_env_config():
    ''' Reads ITER8 config information for env variables'''
    config = {}

    # log level
    # override with environment variable
    config[constants.LOG_LEVEL] = os.getenv(constants.ITER8_ANALYTICS_LOG_LEVEL_ENV, \
        constants.LOG_LEVEL_DEFAULT_LEVEL)

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
