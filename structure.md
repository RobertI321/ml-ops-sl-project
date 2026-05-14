# Stream Learning MLOps Pipeline

A production-grade MLOps pipeline built around Stream Learning, where a model continuously updates on incoming live data, handles concept drift, and is served via a REST API.

---

## Setup
- [ ] Create project folder and open in VSCode
- [ ] Initialize git repo (`git init`)
- [ ] Create and activate virtual environment
- [ ] Create `requirements.txt`
- [ ] Create `.gitignore` — add: `venv/`, `mlruns/`, `__pycache__/`, `.env`
- [ ] Create folder structure: `src/`, `tests/`, `.github/workflows/`
- [ ] Initial commit

---

## Phase 1 — Understand the data
- [ ] Read the API documentation
- [ ] Write a scratch script that fetches one response and prints it raw
- [ ] Decide what your prediction target is
- [ ] Decide what features you will derive from each event
- [ ] Decide when the label arrives
- [ ] Confirm you can simulate a stream by polling repeatedly
- [ ] Write clean `src/ingest.py`

---

## Phase 2 — Stream Learning model
- [ ] Install River
- [ ] Write `src/train.py` — fetch event → predict → receive label → update model
- [ ] Confirm the model is learning (AUC improving over time)
- [ ] Add ADWIN drift detector
- [ ] Confirm drift events are being detected and printed
- [ ] Add event counter and triggering mechanism (serialize every T events)

---

## Phase 3 — MLflow
- [ ] Install MLflow
- [ ] Start MLflow server locally and confirm UI is accessible
- [ ] Log AUC every N events inside the training loop
- [ ] Log drift events as run tags
- [ ] Register serialized model versions to MLflow model registry
- [ ] Confirm new versions appear in the registry as the stream runs

---

## Phase 4 — Flask inference API
- [ ] Write `src/serve.py` — Flask app that loads the latest model version from MLflow
- [ ] Add a `/predict` endpoint
- [ ] Add a background thread that polls MLflow for new versions and hot-swaps
- [ ] Test the endpoint manually with a sample request
- [ ] Confirm the model updates without restarting the server

---

## Phase 5 — Docker and Docker Compose
- [ ] Write `Dockerfile` for the inference service
- [ ] Confirm the Flask app runs inside the container
- [ ] Write `docker-compose.yml` with three services: ingest/train, MLflow, serve
- [ ] Confirm all services start and can communicate
- [ ] Confirm the full pipeline runs end to end inside Docker Compose

---

## Phase 6 — CI/CD
- [ ] Write `.github/workflows/ci.yml`
- [ ] Add a step that installs dependencies and runs tests
- [ ] Write at least one test in `tests/`
- [ ] Push to GitHub and confirm the workflow passes
- [ ] Add a step that builds the Docker image on successful tests

---

## Phase 7 — Demo readiness
- [ ] Full pipeline runs from cold start with `docker compose up`
- [ ] Live prediction being served via `/predict`
- [ ] MLflow UI shows metrics and model versions
- [ ] Drift events visible in MLflow
- [ ] README updated with how to run the project