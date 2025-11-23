# Streamlit UI — Docker & Kubernetes Deployment

This bundle contains everything you need to containerize and deploy your `chat_ui.py` Streamlit app.
It assumes your backend API exposes a `/chat` endpoint and that the UI reads its URL from the `API_URL_CHAT` environment variable.

---

## Files (your structure)

- `ops/docker/Dockerfile` — builds a slim image for the Streamlit UI
- `ops/docker/.dockerignore` — keeps images small
- `ops/docker/docker-compose.yml` — local multi-container test (optional)
- `ops/k8s/namespace.yaml` — optional logical namespace
- `ops/k8s/configmap.yaml` — holds `API_URL_CHAT` for the UI pods
- `ops/k8s/deployment-ui.yaml` — Deployment for UI (2 replicas)
- `ops/k8s/service-ui.yaml` — ClusterIP Service for UI
- `ops/k8s/ingress.yaml` — Ingress to expose UI externally
- `deploy.sh` — helper script to apply the manifests

---

## Prerequisite: make the API URL configurable in your code

In `chat_ui.py`, ensure you read the backend URL from an environment variable:

```python
import os
API_URL_CHAT = os.getenv("API_URL_CHAT", "http://127.0.0.1:8000/chat")
