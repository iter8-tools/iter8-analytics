[![Build Status](https://travis-ci.com/iter8-tools/iter8-analytics.svg?branch=master)](https://travis-ci.com/iter8-tools/iter8-analytics)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

# iter8-analytics

> iter8 enables statistically robust continuous experimentation of microservices in your CI/CD pipelines.

For in-depth information about how to use iter8, visit [iter8.tools](https://iter8.tools).

## In this README:

- [Introduction](#introduction)
- [Repositories](#repositories)
- [Developers](#developers)

## Introduction
Use an iter8 experiment to safely expose competing versions of a service to application traffic, gather in-depth insights about key metrics for your microservice versions, and intelligently rollout the best version of your service.

Iter8’s expressive model of cloud experimentation supports a variety of CI/CD scenarios. Using an iter8 experiment, you can:

1. Run a conformance test with a single version of a microservice.
2. Perform a canary release with two versions, a baseline and a candidate. Iter8 will shift application traffic safely and gradually to the candidate, if it meets the criteria you specify in the experiment.
3. Perform an A/B test with two versions – a baseline and a candidate. Iter8 will identify and shift application traffic safely and gradually to the winner, where the winning version is defined by the criteria you specify in the experiment.
4. Perform an A/B/n test with multiple versions – a baseline and multiple candidates. Iter8 will identify and shift application traffic safely and gradually to the winner.

Under the hood, iter8 uses advanced Bayesian learning techniques coupled with multi-armed bandit approaches to compute a variety of statistical assessments for your microservice versions, and uses them to make robust traffic control and rollout decisions.

## Repositories

The components of iter8 are divided across a few github repositories.

- [iter8](https://github.com/iter8-tools/iter8) The main iter8 repository containing the kubernetes controller that orchestrates iter8's experiments.
- [iter8-analytics](https://github.com/iter8-tools/iter8-analytics) This repository containing the iter8-analytics component.
- [iter8-trend](https://github.com/iter8-tools/iter8-trend) The repository contains the iter8-trend component.

In addition,
- iter8's extensions to Kiali is contained in [kiali](https://github.com/kiali/kiali), [kiali-ui](https://github.com/kiali/kiali-ui), and [k-charted](https://github.com/kiali/k-charted). 
- iter8's extensions to Kui is contained in [kui](https://github.com/IBM/kui). 


## Developers

This section is for iter8 developers and contains documentation on running and testing iter8-analytics locally.

### Running iter8-analytics v1.0.0 locally
The following instructions have been tested in a Python 3.7.4 virtual environment.

```
1. git clone git@github.com:iter8-tools/iter8-analytics.git
2. cd iter8-analytics
3. pip install -r requirements.txt 
4. pip install -e .
5. export ITER8_ANALYTICS_METRICS_BACKEND_URL=<URL of your prometheus service>
6. cd iter8_analytics
7. python fastapi_app.py 
```
Navigate to http://localhost:5555/docs on your browser. You can interact with the iter8-analytics service and read its API documentation here. When you `POST` a request to iter8-analytics, it interacts with Prometheus -- make sure your Prometheus URL in step 5 is accessible if you want the `POST` to work.

### Running unit tests for iter8-analytics v1.0.0 locally
The following instructions have been tested in a Python 3.7.4 virtual environment.

```
1. git clone git@github.com:iter8-tools/iter8-analytics.git
2. cd iter8-analytics
3. pip install -r requirements.txt 
4. pip install -r test-requirements.txt
5. pip install -e .
6. export ITER8_ANALYTICS_METRICS_BACKEND_URL=<URL of your prometheus service>
7. coverage run --source=iter8_analytics --omit="*/__init__.py" -m pytest
```
You can see the coverage report by opening `htmlcov/index.html` on your browser. The prometheus URL in step 6 is a dummy URL since all Prometheus calls are mocked in unit tests.
