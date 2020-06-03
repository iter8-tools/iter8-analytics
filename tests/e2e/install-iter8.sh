#!/usr/bin/env bash

# Exit on error
set -e

# Install Iter8 controller manager
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/v0.2/install/iter8-controller.yaml

# Build a new Iter8-analytics image based on the new code
IMG=iter8-analytics:test make docker-build

# Install Helm
curl -fsSL https://get.helm.sh/helm-v2.16.7-linux-amd64.tar.gz | tar xvzf - && sudo mv linux-amd64/helm /usr/local/bin

# Create new Helm template based on the new image
helm template install/kubernetes/helm/iter8-analytics/ --name iter8-analytics \
--set image.repository=iter8-analytics \
--set image.tag=test \
--set image.pullPolicy=IfNotPresent \
> install/kubernetes/iter8-analytics.yaml

cat install/kubernetes/iter8-analytics.yaml

# Install Iter8-analytics
kubectl apply -f install/kubernetes/iter8-analytics.yaml

# Check if Iter8 pods are all up and running. However, sometimes
# `kubectl apply` doesn't register for `kubectl wait` before, so
# adding 1 sec wait time for the operation to fully register
sleep 1
kubectl wait --for=condition=Ready pods --all -n iter8 --timeout=300s
kubectl -n iter8 get pods
