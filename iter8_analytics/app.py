import logging
import os
import sys

from flask import Flask, Blueprint, redirect

from iter8_analytics.api.restplus import api
from iter8_analytics.api.health.endpoints.health import health_namespace
from iter8_analytics.api.analytics.endpoints.analytics \
    import analytics_namespace
from iter8_analytics.api.analytics.endpoints.analytics \
    import experiment_namespace
import iter8_analytics.constants as constants

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


def config_env():
    '''Reads the environment variables that control the server behavior and
    populates the config dictionary'''
    if not os.getenv(constants.ITER8_ANALYTICS_METRICS_BACKEND_URL_ENV):
        logging.getLogger(__name__).critical(
            u'The environment variable {0} was not set. '
            'Example of a valid value: "http://localhost:9090". '
            'Aborting!'.format(
                constants.ITER8_ANALYTICS_METRICS_BACKEND_URL_ENV))
        sys.exit(1)

    logging.getLogger(__name__).info('Configuring iter8 analytics server')

    app.config[constants.ITER8_ANALYTICS_SERVER_PORT_ENV] = \
        os.getenv(constants.ITER8_ANALYTICS_SERVER_PORT_ENV, 5555)

    logging.getLogger(__name__).info(
        u'The iter8 analytics server will listen on port {0}. '
        'This value can be set by the environment variable {1}'.format(
            app.config[constants.ITER8_ANALYTICS_SERVER_PORT_ENV],
            constants.ITER8_ANALYTICS_SERVER_PORT_ENV))

    debug_mode = os.getenv(constants.ITER8_ANALYTICS_DEBUG_ENV, 'false')
    if debug_mode == '1' or str.lower(debug_mode) == 'true':
        app.config[constants.ITER8_ANALYTICS_DEBUG_ENV] = True
    else:
        app.config[constants.ITER8_ANALYTICS_DEBUG_ENV] = False
    logging.getLogger(__name__).info(u'Debug mode: {0}'.format(debug_mode))


def initialize(flask_app):
    '''Initializes the Flask application'''
    blueprint = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    api.init_app(blueprint)
    api.add_namespace(health_namespace)
    api.add_namespace(analytics_namespace)
    api.add_namespace(experiment_namespace)
    flask_app.register_blueprint(blueprint)
    config_env()


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
        port=int(app.config[constants.ITER8_ANALYTICS_SERVER_PORT_ENV]))
