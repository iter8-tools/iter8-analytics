[![Build Status](https://travis-ci.com/iter8-tools/iter8-analytics.svg?branch=master)](https://travis-ci.com/iter8-tools/iter8-analytics)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

# iter8-analytics

> iter8 enables statistically robust continuous experimentation of microservices in your CI/CD pipelines.

For in-depth information about how to use iter8, visit [iter8.tools](https://iter8.tools).

## In this README:

- [Introduction](#introduction)
- [Developers](#developers)

## Introduction
Use an iter8 experiment to safely expose competing versions of a service to application traffic, gather in-depth insights about key metrics for your microservice versions, and intelligently rollout the best version of your service.

Iter8’s expressive model of cloud experimentation supports a variety of CI/CD scenarios. Using an iter8 experiment, you can:

1. Run a conformance test with a single version of a microservice.
2. Perform a canary release with two versions, a baseline and a candidate. Iter8 will shift application traffic safely and gradually to the candidate, if it meets the criteria you specify in the experiment.
3. Perform an A/B test with two versions – a baseline and a candidate. Iter8 will identify and shift application traffic safely and gradually to the winner, where the winning version is defined by the criteria you specify in the experiment.
4. Perform an A/B/n test with multiple versions – a baseline and multiple candidates. Iter8 will identify and shift application traffic safely and gradually to the winner.

Under the hood, iter8 uses advanced Bayesian learning techniques coupled with multi-armed bandit approaches to compute a variety of statistical assessments for your microservice versions, and uses them to make robust traffic control and rollout decisions.

## Developers

This section is for iter8 developers and contains documentation on running and testing iter8-analytics locally.

### Running iter8-analytics v2.x locally
The following instructions have been tested in a Python 3.9.0 virtual environment.

```
1. git clone git@github.com:iter8-tools/iter8-analytics.git
2. cd iter8-analytics
3. pip install -r requirements.txt 
4. pip install -e .
5. cd iter8_analytics
6. python fastapi_app.py 
```
Navigate to http://localhost:8080/docs on your browser. You can interact with the iter8-analytics service and read its API documentation here. The iter8-analytics APIs are intended to work with metric databases, and use Kubernetes secrets for obtaining the required authentication information for querying the metric DBs.

### Running unit tests for iter8-analytics v2.x locally
The following instructions have been tested in a Python 3.9.0 virtual environment.

```
1. git clone git@github.com:iter8-tools/iter8-analytics.git
2. cd iter8-analytics
3. pip install -r requirements.txt 
4. pip install -r test-requirements.txt
5. pip install -e .
6. coverage run --source=iter8_analytics --omit="*/__init__.py" -m pytest
```
You can see the coverage report by opening `htmlcov/index.html` on your browser.
