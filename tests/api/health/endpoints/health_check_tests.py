
import unittest
import logging
log = logging.getLogger(__name__)
from fastapi.testclient import TestClient
from iter8_analytics import fastapi_app
class TestHealthCheckAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup common to all tests in this class"""

        cls.client = TestClient(fastapi_app.app)
        log.info('Completed initialization for FastAPI based  REST API tests')

    def test_fastapi(self):
        # fastapi endpoint
        endpoint = "/health_check"

        log.info("\n\n\n")
        log.info('===TESTING FASTAPI ENDPOINT')
        log.info("Test iter8 analytics health")

        # Call the FastAPI endpoint via the test client
        resp = self.client.get(endpoint)
        self.assertEqual(resp.status_code, 200, msg = "Successful request")
