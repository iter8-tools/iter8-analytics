import requests_mock
import logging
import json

from fastapi.testclient import TestClient

import iter8_analytics.constants as constants
from iter8_analytics import fastapi_app
import iter8_analytics.config as config

from iter8_analytics.api.analytics.types import *
from iter8_analytics.api.analytics.endpoints.examples import eip_example

env_config = config.get_env_config()
fastapi_app.config_logger(env_config[constants.LOG_LEVEL])
logger = logging.getLogger('iter8_analytics')

test_client = TestClient(fastapi_app.app)
metrics_backend_url = env_config[constants.METRICS_BACKEND_CONFIG_URL]
metrics_endpoint = f'{metrics_backend_url}/api/v1/query'

class TestUnifiedAnalyticsAPI:
    def test_fastapi(self):
        # fastapi endpoint
        with requests_mock.mock(real_http=True) as m:
            m.get(metrics_endpoint, json=json.load(open("tests/data/prometheus_sample_response.json")))

            endpoint = "/assessment"

            # fastapi post data
            eip = ExperimentIterationParameters(** eip_example)

            logger.info("\n\n\n")
            logger.info('===TESTING FASTAPI ENDPOINT')
            logger.info("Test request with some required parameters")

            # Call the FastAPI endpoint via the test client
            resp = test_client.post(endpoint, json = eip_example)
            it8_ar_example = Iter8AssessmentAndRecommendation(** resp.json())
            assert resp.status_code == 200
