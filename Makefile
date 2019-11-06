IMG ?= iter8-analytics:latest

ITER8_ANALYTICS_METRICS_BACKEND_URL ?= http://localhost:9090

all: build-default

clean-pyc:
	find iter8_analytics -type f \
	  \( -name '__pycache__' -o -name '*.pyc' -o -name '*.pyo' -o -name '*~' \) \
	-exec rm --force {} +

# Deploy controller to the Kubernetes cluster configured in $KUBECONFIG or ~/.kube/config
deploy: 
	helm template install/kubernetes/helm/iter8-analytics \
	  --name iter8-analytics \
	  --set image.repository=`echo ${IMG} | cut -f1 -d':'` \
	  --set image.tag=`echo ${IMG} | cut -f2 -d':'` \
	| kubectl apply -f -

docker-run: docker-cleanup docker-build
	docker run -d --name iter8-analytics \
	  -p 5555:5555 \
	  -e ITER8_ANALYTICS_METRICS_BACKEND_URL=$ITER8_ANALYTICS_METRICS_BACKEND_URL \
	${IMG}

docker-build: clean-pyc
	docker build . -t ${IMG}
	
docker-push:
	docker push ${IMG}

docker-cleanup:
	docker rm -f iter8-analytics 2>/dev/null

build-default:
	helm template install/kubernetes/helm/iter8-analytics \
   		--name iter8-analytics \
	> install/kubernetes/iter8-analytics.yaml
