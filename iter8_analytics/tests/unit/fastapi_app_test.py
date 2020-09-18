import requests_mock
import logging
import json
import os
import copy

from fastapi.testclient import TestClient

import iter8_analytics.constants as constants
from iter8_analytics import fastapi_app
import iter8_analytics.config as config

from iter8_analytics.api.types import *
from iter8_analytics.tests.unit.data.inputs.inputs import eip_example

env_config = config.get_env_config()
logger = logging.getLogger('iter8_analytics')
if not logger.hasHandlers():
    fastapi_app.config_logger(env_config[constants.LOG_LEVEL])

test_client = TestClient(fastapi_app.app)
metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'


class TestUnifiedAnalyticsAPI:
    def test_fastapi(self):
        # fastapi endpoint
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            endpoint = "/assessment"

            # fastapi post data
            eip = ExperimentIterationParameters(** eip_example)

            # Call the FastAPI endpoint via the test client
            resp = test_client.post(endpoint, json=eip_example)
            iter8_ar_example = Iter8AssessmentAndRecommendation(** resp.json())
            assert resp.status_code == 200

    def test_fastapi_with_empty_last_state(self):
        # fastapi endpoint
        with requests_mock.mock(real_http=True) as m:
            file_path = os.path.join(os.path.dirname(__file__), 'data/prom_responses',
                                     'prometheus_sample_response.json')
            m.get(metrics_endpoint, json=json.load(open(file_path)))

            endpoint = "/assessment"

            # fastapi post data
            eg = copy.deepcopy(eip_example)
            eg['last_state'] = {}
            eip = ExperimentIterationParameters(** eg)

            # Call the FastAPI endpoint via the test client
            resp = test_client.post(endpoint, json=eip_example)
            it8_ar_example = Iter8AssessmentAndRecommendation(** resp.json())
            assert resp.status_code == 200
