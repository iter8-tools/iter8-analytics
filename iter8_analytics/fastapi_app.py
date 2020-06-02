"""Fast API based iter8 analytics service.
"""
# core python dependencies
import logging
import os
import sys

# external dependencies
from fastapi import FastAPI, Body
import uvicorn
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# iter8 dependencies
from iter8_analytics.api.analytics.types import ExperimentIterationParameters, Iter8AssessmentAndRecommendation
#from iter8_analytics.api.analytics.experiment import Experiment
import iter8_analytics.api.analytics.experiment as experiment
from iter8_analytics.api.analytics.endpoints.examples import eip_example
import iter8_analytics.constants as constants
import iter8_analytics.config as config

# main FastAPI app
app = FastAPI()

@app.post("/assessment", response_model=Iter8AssessmentAndRecommendation)
def provide_assessment_for_this_experiment_iteration(eip: ExperimentIterationParameters = Body(..., example=eip_example)):
    """
    POST iter8 experiment iteration data and obtain assessment of how the versions are performing and recommendations on how to split traffic based on multiple strategies.
    \f
    :body eip: ExperimentIterationParameters
    """
    return experiment.Experiment(eip).run()


@app.get("/health_check")
def provide_iter8_analytics_health():
    """Get iter8 analytics health status"""
    return {"status": "Ok"}


def config_logger(log_level = "debug"):
    """Configures the global logger

    Args:
        log_level (str): log level ('debug', 'info', ...)
    """
    logger = logging.getLogger('iter8_analytics')
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
    logging.getLogger('iter8_analytics').info("Configured logger")

if __name__ == '__main__':
    config_logger(config.env_config[constants.LOG_LEVEL])
    uvicorn.run('fastapi_app:app', host='0.0.0.0', port=int(config.env_config[constants.ANALYTICS_SERVICE_PORT]), log_level=config.env_config[constants.LOG_LEVEL])
