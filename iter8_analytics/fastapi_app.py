# Module dependencies
from fastapi import FastAPI, Body
import uvicorn

import logging
import os
import sys

# iter8 stuff
from iter8_analytics.api.analytics.experiment_iteration_request import ExperimentIterationParameters
from iter8_analytics.api.analytics.experiment_iteration_response import Iter8AssessmentAndRecommendation
from iter8_analytics.api.analytics.experiment import Experiment
from iter8_analytics.api.analytics.endpoints.examples import eip_example
import iter8_analytics.constants as constants

app = FastAPI()

@app.post("/assessment", response_model=Iter8AssessmentAndRecommendation)
def provide_assessment_for_this_experiment_iteration(eip: ExperimentIterationParameters = Body(..., example=eip_example)):
    """
      POST iter8 experiment iteration data and obtain assessment of how the versions are performing and recommendations on how to split traffic based on multiple strategies.
      """
    return Experiment(eip).run()


@app.get("/health_check")
def provide_iter8_analytics_health():
    """Get iter8 analytics health status"""
    return {"status": "Ok"}


def config_logger(log_level):
    """Configures the global logger"""
    logger = logging.getLogger('')
    handler = logging.StreamHandler()

    if str.lower(log_level) == 'info':
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    elif str.lower(log_level) == 'warning':
        logger.setLevel(logging.WARNING)
        handler.setLevel(logging.WARNING)
    elif str.lower(log_level) == 'error':
        logger.setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)
    elif str.lower(log_level) == 'critical':
        logger.setLevel(logging.CRITICAL)
        handler.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s'
            ' - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logging.getLogger(__name__).info("Configured logger")


def get_env_config():
    """
      Reads the environment variables that control the server behavior and populates the config dictionary
      """

    if not os.getenv(constants.METRICS_BACKEND_URL_ENV):
        logging.getLogger(__name__).critical(
            u'The environment variable {0} was not set. '
            'Example of a valid value: "http://localhost:9090". '
            'Aborting!'.format(constants.METRICS_BACKEND_URL_ENV))
        sys.exit(1)

    logging.getLogger(__name__).info('Configuring iter8 analytics server')

    config = {}
    config[constants.ITER8_ANALYTICS_LOG_LEVEL_ENV] = os.getenv(
        constants.ITER8_ANALYTICS_LOG_LEVEL_ENV, 'debug')

    config[constants.ANALYTICS_SERVICE_PORT] = os.getenv(
        constants.ANALYTICS_SERVICE_PORT_ENV, 5555)

    logging.getLogger(__name__).info(
        u'The iter8 analytics server will listen on port {0}. '
        'This value can be set by the environment variable {1}'.format(config[constants.ANALYTICS_SERVICE_PORT], constants.ANALYTICS_SERVICE_PORT_ENV))

    return config


if __name__ == '__main__':
    env_config = get_env_config()
    config_logger(env_config[constants.ITER8_ANALYTICS_LOG_LEVEL_ENV])
    logging.getLogger(__name__).info('Starting iter8 analytics server')

    uvicorn.run('fastapi_app:app', host='0.0.0.0', port=int(env_config[constants.ANALYTICS_SERVICE_PORT]), log_level=env_config[constants.ITER8_ANALYTICS_LOG_LEVEL_ENV])
