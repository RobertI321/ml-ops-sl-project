# Stream Learning MLOps Pipeline

A production-grade MLOps pipeline built around Stream Learning, where a model continuously updates on incoming live data, handles concept drift, and is served via a REST API.

---

## Setup
- [x] Create project folder and open in VSCode
- [x] Initialize git repo (`git init`)
- [x] Create and activate virtual environment
- [x] Create `requirements.txt`
- [x] Create `.gitignore` — add: `venv/`, `mlruns/`, `__pycache__/`, `.env`
- [x] Create folder structure: `src/`, `tests/`, `.github/workflows/`
- [x] Initial commit

---

## Phase 1 — Understand the data
- [x] Read the API documentation
- [x] Write a scratch script that fetches one response and prints it raw
- [x] Decide what your prediction target is — price direction up/down
- [x] Decide what features you will derive from each event
- [x] Decide when the label arrives — on the next poll
- [x] Confirm you can simulate a stream by polling repeatedly
- [x] Write clean `src/ingest.py`

---

## Phase 2 — Kafka
- [x] Add Kafka and Zookeeper to `docker-compose.yml`
- [x] Write `Dockerfile.ingest`
- [x] Add Kafka producer to `ingest.py`
- [x] Confirm messages are arriving in the topic
- [x] Confirm ingest container runs stably without crashing

---

## Phase 3 — Stream Learning model
- [ ] Write `src/train.py` — consume from Kafka → predict → update model
- [ ] Confirm the model is learning (AUC improving over time)
- [ ] Add ADWIN drift detector
- [ ] Confirm drift events are being detected and printed
- [ ] Add event counter and triggering mechanism (serialize every T events)

---

## Phase 4 — MLflow
- [ ] Add MLflow service to `docker-compose.yml`
- [ ] Log AUC every N events inside the training loop
- [ ] Log drift events as run tags
- [ ] Register serialized model versions to MLflow model registry
- [ ] Confirm new versions appear in the registry as the stream runs

---

## Phase 5 — Flask inference API
- [ ] Write `src/serve.py` — Flask app that loads the latest model version from MLflow
- [ ] Add a `/predict` endpoint
- [ ] Add a background thread that polls MLflow for new versions and hot-swaps
- [ ] Test the endpoint manually with a sample request
- [ ] Confirm the model updates without restarting the server
- [ ] Add serve service to `docker-compose.yml`

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