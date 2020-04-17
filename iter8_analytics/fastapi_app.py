# Module dependencies
from fastapi import FastAPI, Body

# iter8 stuff
from iter8_analytics.api.analytics.experiment_iteration_request import ExperimentIterationParameters
from iter8_analytics.api.analytics.experiment_iteration_response import Iter8AssessmentAndRecommendation
from iter8_analytics.api.analytics.experiment import  Experiment
from iter8_analytics.api.analytics.endpoints.examples import eip_example

app = FastAPI()

@app.post("/assessment", response_model=Iter8AssessmentAndRecommendation)
def provide_assessment_for_this_experiment_iteration(eip: ExperimentIterationParameters = Body(..., example=eip_example)):
    """
      POST iter8 experiment iteration data and obtain assessment of how the versions are performing and recommendations on how to split traffic based on multiple strategies.
      """
    return Experiment(eip).run()



@app.get("/health_check")
def provide_iter8_analytics_health():
    """
      Get iter8 analytics health status
      """
    return {"status": "Ok"}