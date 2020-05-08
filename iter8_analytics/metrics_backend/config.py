import iter8_analytics.constants as constants
import logging

log = logging.getLogger(__name__)

class MetricsBackendConfig:
    _backend = {
        constants.METRICS_BACKEND_CONFIG_URL: constants.METRICS_BACKEND_CONFIG_DEFAULT_URL,
        constants.METRICS_BACKEND_CONFIG_TYPE: constants.METRICS_BACKEND_CONFIG_TYPE_PROMETHEUS,
        constants.METRICS_BACKEND_CONFIG_AUTH: {
            constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE,
        }
    }

    @classmethod
    def addMetricsBackendConfig(cls, url, authentication):
        cls._backend[constants.METRICS_BACKEND_CONFIG_URL] = url
        cls._backend[constants.METRICS_BACKEND_CONFIG_AUTH] = authentication
        if not (constants.METRICS_BACKEND_CONFIG_AUTH_TYPE in authentication):
            cls._backend[constants.METRICS_BACKEND_CONFIG_AUTH][constants.METRICS_BACKEND_CONFIG_AUTH_TYPE] = \
                constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE

    @classmethod
    def getUrl(cls):
        return cls._backend[constants.METRICS_BACKEND_CONFIG_URL]

    @classmethod
    def getAuthentication(cls):
        return cls._backend[constants.METRICS_BACKEND_CONFIG_AUTH]

    @classmethod
    def getAuthenticationType(cls):
        return cls._backend[constants.METRICS_BACKEND_CONFIG_AUTH][constants.METRICS_BACKEND_CONFIG_AUTH_TYPE]