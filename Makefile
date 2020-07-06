IMG ?= iter8-analytics:latest

ITER8_ANALYTICS_METRICS_BACKEND_URL ?= http://localhost:9090
ITER8_ANALYTICS_DEBUG_ENV ?= false

all: build-default

clean-pyc:
	find iter8_analytics -type f \
	  \( -name '__pycache__' -o -name '*.pyc' -o -name '*.pyo' -o -name '*~' \) \
	-exec rm -f {} +

# Deploy analytics engine to the Kubernetes cluster configured in $KUBECONFIG or ~/.kube/config
deploy:
	helm template install/kubernetes/helm/iter8-analytics \
	  --name iter8-analytics \
	  --set image.repository=`echo ${IMG} | cut -f1 -d':'` \
	  --set image.tag=`echo ${IMG} | cut -f2 -d':'` \
	| kubectl apply -f -

docker-run: docker-cleanup docker-build
	docker run -d --name iter8-analytics \
	  -p 5555:5555 \
	  -e ITER8_ANALYTICS_SERVER_PORT=5555 \
	  -e ITER8_ANALYTICS_METRICS_BACKEND_URL=${ITER8_ANALYTICS_METRICS_BACKEND_URL} \
	  -e ITER8_ANALYTICS_DEBUG_ENV=${ITER8_ANALYTICS_DEBUG_ENV} \
	${IMG}

docker-build: clean-pyc
	docker build . -t ${IMG}

docker-push:
	docker push ${IMG}

docker-cleanup:
	docker rm -f iter8-analytics 2>/dev/null || true

build-default:
	echo '# Generated by make build-default; DO NOT EDIT' > install/kubernetes/iter8-analytics.yaml
	helm template install/kubernetes/helm/iter8-analytics \
   		--name iter8-analytics \
	>> install/kubernetes/iter8-analytics.yaml

.PHONY: changelog
changelog:
	@sed -n '/$(ver)/,/=====/p' CHANGELOG | grep -v $(ver) | grep -v "====="

test:
	nosetests --exe --with-coverage --cover-package=iter8_analytics --cover-html --cover-html-dir=code_coverage --ignore-files=".*_test.py"
	coverage run --source=iter8_analytics --omit="*/__init__.py" -m pytest
	coverage html
