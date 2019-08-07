#!/bin/bash

SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


echo ""
echo ""
echo "===================================="
echo "=== STARTING TESTS with NOSETESTS==="
echo "===================================="
echo ""
echo ""

set -o xtrace
cd $SCRIPTDIR/..

DEFAULT_PROMETHEUS_URL="http://localhost:9090"

if [ -z "${ITER8_ANALYTICS_METRICS_BACKEND_URL}" ]; then
   export ITER8_ANALYTICS_METRICS_BACKEND_URL=$DEFAULT_PROMETHEUS_URL
fi

nosetests --exe --with-coverage --cover-package=iter8_analytics --cover-html --cover-html-dir=$SCRIPTDIR/../code_coverage
