#!/usr/bin/env bash
set -euo pipefail

# Apply all manifests from ops/k8s
kubectl apply -f ops/k8s/namespace.yaml
kubectl apply -f ops/k8s/configmap.yaml
kubectl apply -f ops/k8s/deployment-ui.yaml
kubectl apply -f ops/k8s/service-ui.yaml
kubectl apply -f ops/k8s/ingress.yaml

echo ">>> Deployed. Check resources with:"
echo "    kubectl -n ai-platform get all"
