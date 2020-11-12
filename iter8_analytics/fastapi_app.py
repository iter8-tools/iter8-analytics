"""Fast API based iter8 analytics service.
"""
# core python dependencies
import logging

# external dependencies
from fastapi import FastAPI, Body
import uvicorn

# iter8 dependencies
from iter8_analytics.api.types import \
    ExperimentIterationParameters, Iter8AssessmentAndRecommendation
#from iter8_analytics.api.analytics.experiment import Experiment
import iter8_analytics.api.experiment as experiment
from iter8_analytics.api.examples import eip_example
import iter8_analytics.constants as constants
import iter8_analytics.config as config

# v2 imports
from iter8_analytics.api.v2.types import  ExperimentResource, \
    AggregatedMetrics, VersionAssessments, \
    WinnerAssessment, Weights, Analysis
from iter8_analytics.api.v2.examples import er_example, er_example_step1, \
    er_example_step2, er_example_step3
from iter8_analytics.api.v2.experiment import get_version_assessments, get_winner_assessment, \
     get_weights, get_analytics_results
from iter8_analytics.api.v2.metrics import get_aggregated_metrics

# main FastAPI app
app = FastAPI()


@app.post("/assessment", response_model=Iter8AssessmentAndRecommendation)
def provide_assessment_for_this_experiment_iteration(
        eip: ExperimentIterationParameters = Body(..., example=eip_example)):
    """
    POST iter8 experiment iteration data and obtain assessment of how
    the versions are performing and recommendations on how to split traffic
    based on multiple strategies.
    \f
    :body eip: ExperimentIterationParameters
    """
    run_result = experiment.Experiment(eip).run()
    return run_result


@app.get("/health_check")
def provide_iter8_analytics_health():
    """Get iter8 analytics health status"""
    return {"status": "Ok"}

@app.post("/v2/aggregated_metrics", response_model=AggregatedMetrics, \
    response_model_exclude_unset=True)
def provide_aggregated_metrics(
    er: ExperimentResource = Body(..., example=er_example)):
    """
    POST iter8 2.0 experiment resource and metric resources and obtain aggregated metrics.
    \f
    :body er: ExperimentResource
    """
    aggregated_metrics = get_aggregated_metrics(er)
    return aggregated_metrics

@app.post("/v2/version_assessments", response_model=VersionAssessments)
def provide_version_assessments(
    experiment_resource: ExperimentResource = Body(..., example=er_example_step1)):
    """
    POST iter8 2.0 experiment resource, whose status includes aggregated metrics,
    and obtain version assessments.
    \f
    :body er: ExperimentResource
    """
    version_assessments = get_version_assessments(experiment_resource)
    return version_assessments

@app.post("/v2/winner_assessment", response_model=WinnerAssessment)
def provide_winner_assessment(
    experiment_resource: ExperimentResource = Body(..., example=er_example_step2)):
    """
    POST iter8 2.0 experiment resource, whose status includes
    aggregated metrics/version_assessments, and obtain winner assessment.
    \f
    :body er: ExperimentResource
    """
    winner_assessment = get_winner_assessment(experiment_resource)
    return winner_assessment

@app.post("/v2/weights", response_model=Weights)
def provide_weights(
    experiment_resource: ExperimentResource = Body(..., example=er_example_step3)):
    """
    POST iter8 2.0 experiment resource, whose status includes
    aggregated metrics/version_assessments/winner assessment,
    and obtain weights.
    \f
    :body er: ExperimentResource
    """
    weights = get_weights(experiment_resource)
    return weights

@app.post("/v2/analytics_results", response_model=Analysis)
def provide_analytics_results(
    er: ExperimentResource = Body(..., example=er_example)):
    """
    POST iter8 2.0 experiment resource and metric resources and get analytics results.
    \f
    :body er: ExperimentResource
    """
    analytics_results = get_analytics_results(er)
    return analytics_results

def config_logger(log_level="debug"):
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
    logging.getLogger('iter8_analytics').debug("Configured logger")


if __name__ == '__main__':
    config_logger(config.env_config[constants.LOG_LEVEL])
    uvicorn.run('fastapi_app:app',
                host='0.0.0.0',
                port=int(config.env_config[constants.ANALYTICS_SERVICE_PORT]),
                log_level=config.env_config[constants.LOG_LEVEL])
