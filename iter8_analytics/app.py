import logging
import os
import sys
import yaml

from flask import Flask, Blueprint, redirect

from iter8_analytics.api.restplus import api
from iter8_analytics.api.health.endpoints.health import health_namespace
from iter8_analytics.api.analytics.endpoints.analytics \
    import analytics_namespace
from iter8_analytics.api.analytics.endpoints.analytics \
    import experiment_namespace
import iter8_analytics.constants as constants
from iter8_analytics.metrics_backend.config import MetricsBackendConfig

#  Create a Flask application
app = Flask(__name__)

# Make sure we can serve requests to endpoints with or without trailing slashes
app.url_map.strict_slashes = False

# Disable Flask-Restplus X-Fields header used for partial object fetching
app.config['RESTPLUS_MASK_SWAGGER'] = False


@app.after_request
def modify_headers(response):
    '''Sets the server HTTP header returned to the clients for all requests
    to hide the runtime information'''
    response.headers['server'] = 'iter8 Analytics'
    return response


def config_logger():
    '''Configures the global logger'''
    logger = logging.getLogger('')
    handler = logging.StreamHandler()
    debug_mode = os.getenv(constants.ITER8_ANALYTICS_DEBUG_ENV, 'false')
    if debug_mode == '1' or str.lower(debug_mode) == 'true':
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s'
            ' - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logging.getLogger(__name__).info("Configured logger")

def read_config_file():
    configFile = os.getenv(constants.METRICS_BACKEND_CONFIGFILE_ENV, constants.METRICS_BACKEND_DEFAULT_CONFIGFILE)
    logging.getLogger(__name__).info(f"Reading config file: {configFile}")

    try:
        with open(configFile, 'r') as stream:
            try:
                configYaml = yaml.safe_load(stream)
            except yaml.YAMLError:
                logging.getLogger(__name__).warning(f"Unable to parse configuration file {configFile}; ignoring")
                return {}
    except IOError:
        logging.getLogger(__name__).warning(f"Unable to read configuration file {configFile}; ignoring")
        return {}

    # validate metricsBackend config if present
    if constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND in configYaml:
        metricsBackend = configYaml[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND]
        # if backend type is specified, verify that it is in the supported set {prometheus}
        if constants.METRICS_BACKEND_CONFIG_TYPE in metricsBackend:
            if not (metricsBackend[constants.METRICS_BACKEND_CONFIG_TYPE] in [constants.METRICS_BACKEND_CONFIG_TYPE_PROMETHEUS]):
                logging.getLogger(__name__).error(f"Only {constants.METRICS_BACKEND_CONFIG_TYPE_PROMETHEUS} is supported. Ignoring {constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND} configuration.")
                del configYaml[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND]
        # if auth.type is specified, verify tht it is in the supported set {none, basic}
        if constants.METRICS_BACKEND_CONFIG_AUTH in metricsBackend:
            auth = metricsBackend[constants.METRICS_BACKEND_CONFIG_AUTH]
            if constants.METRICS_BACKEND_CONFIG_AUTH_TYPE in auth:
                if not (auth[constants.METRICS_BACKEND_CONFIG_AUTH_TYPE]in [constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE, constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC]):
                    logging.getLogger(__name__).error(f"Only {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_BASIC} (or {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}) authentication supported. Trying {constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE}")
                    configYaml[constants.METRICS_BACKEND_CONFIG_METRICS_BACKEND][constants.METRICS_BACKEND_CONFIG_AUTH][constants.METRICS_BACKEND_CONFIG_AUTH_TYPE] = constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE
    return configYaml
   
def config_app():
    ''' Reads config from config file. Config file default is './config.yaml'
    but can be overwritten by an environment variable METRICS_BACKEND_CONFIGFILE'''
    configMap = read_config_file()

    # port 
    # default value
    app.config[constants.ANALYTICS_SERVICE_PORT] = constants.ANALYTICS_SERVICE_DEFAULT_PORT
    logging.getLogger(__name__).info(f"Default port is: {app.config[constants.ANALYTICS_SERVICE_PORT]}")
    # override with value in configFile
    if constants.ANALYTICS_SERVICE_CONFIGFILE_PORT in configMap:
        app.config[constants.ANALYTICS_SERVICE_PORT] = configMap[constants.ANALYTICS_SERVICE_CONFIGFILE_PORT]
        logging.getLogger(__name__).info(f"Port in config file is: {app.config[constants.ANALYTICS_SERVICE_PORT]}")
    # override with value in env variable
    app.config[constants.ANALYTICS_SERVICE_PORT] = os.getenv(constants.ANALYTICS_SERVICE_PORT_ENV, app.config[constants.ANALYTICS_SERVICE_PORT])
    # log result
    logging.getLogger(__name__).info(f"The iter8 analytics server will listen on port {app.config[constants.ANALYTICS_SERVICE_PORT]}")

    # metrics backend
    # default value defined in MetricsBackendConfig
    # override with value in configFile
    auth = { constants.METRICS_BACKEND_CONFIG_AUTH_TYPE: constants.METRICS_BACKEND_CONFIG_AUTH_TYPE_NONE }
    logging.getLogger(__name__).info(f"Set default auth as: {auth}")
    if constants.METRICS_BACKEND_CONFIGFILE_PROMETHEUS in configMap:
        if constants.METRICS_BACKEND_CONFIGFILE_URL in configMap[constants.METRICS_BACKEND_CONFIGFILE_PROMETHEUS]:
            url = configMap[constants.METRICS_BACKEND_CONFIGFILE_PROMETHEUS][constants.METRICS_BACKEND_CONFIGFILE_URL]
            logging.getLogger(__name__).info(f"Read url from config as: {url}")
        if constants.METRICS_BACKEND_CONFIG_AUTH in configMap[constants.METRICS_BACKEND_CONFIGFILE_PROMETHEUS]:
            auth = configMap[constants.METRICS_BACKEND_CONFIGFILE_PROMETHEUS][constants.METRICS_BACKEND_CONFIG_AUTH]
            logging.getLogger(__name__).info(f"Read auth from config as: {auth}")
        MetricsBackendConfig.addMetricsBackendConfig(url, auth)
    # override with value in environment variable (in which case no )
    if os.getenv(constants.METRICS_BACKEND_URL_ENV):
        url = os.getenv(constants.METRICS_BACKEND_URL_ENV)
        logging.getLogger(__name__).info(f"Read url from env as: {url}")
        MetricsBackendConfig.addMetricsBackendConfig(url, auth)
    # log result
    logging.getLogger(__name__).info(f"The backend metrics server is {MetricsBackendConfig.getUrl()}")
    
    # debug mode
    # default is False
    # currently only specifiable by environment variable
    debug_mode = os.getenv(constants.ITER8_ANALYTICS_DEBUG_ENV, 'false')
    if debug_mode == '1' or str.lower(debug_mode) == 'true':
        app.config[constants.ITER8_ANALYTICS_DEBUG_ENV] = True
    else:
        app.config[constants.ITER8_ANALYTICS_DEBUG_ENV] = False
    # log result
    logging.getLogger(__name__).info(u'Debug mode: {0}'.format(debug_mode))


def initialize(flask_app):
    '''Initializes the Flask application'''
    blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    api.init_app(blueprint)
    api.add_namespace(health_namespace)
    api.add_namespace(analytics_namespace)
    api.add_namespace(experiment_namespace)
    flask_app.register_blueprint(blueprint)
    config_app()


#######
# main function
#######
if __name__ == '__main__':
    config_logger()
    initialize(app)
    logging.getLogger(__name__).info('Starting iter8 analytics server')
    app.run(
        host='0.0.0.0', debug=app.config
        [constants.ITER8_ANALYTICS_DEBUG_ENV],
        port=int(app.config[constants.ANALYTICS_SERVICE_PORT]))
