# Stream Learning MLOps Pipeline

A production-grade MLOps pipeline for real-time BTC/USDT price direction prediction using Stream Learning. Unlike traditional batch ML pipelines, the model continuously updates on every incoming price event, adapts to concept drift (market regime changes), and serves live predictions via a REST API - all running as containerized microservices.

## Architecture

```
Finnhub API → Ingest → Kafka → Train (River HAT) → MLflow → Serve (Flask)
                                                         ↓
                                                    MinIO (artifacts)
```

**Ingest** polls the Finnhub API every 30 seconds for BTC/USDT price data and publishes structured events to a Kafka topic. **Train** consumes those events one by one, updates a HoeffdingAdaptiveTreeClassifier incrementally using prequential evaluation (predict then learn), monitors for concept drift using ADWIN, and serializes model snapshots to MLflow every 10 events. **Serve** loads the latest Production model from the MLflow registry and serves binary predictions (price up or down) via Flask, hot-swapping to new model versions in the background without restarting.

## Prerequisites

Docker and Docker Compose installed. Free Finnhub API key from finnhub.io.

## Quick Start

Clone the repo and create a `.env` file in the project root:

```
API_KEY=your_finnhub_api_key
ACCESS_KEY=your_minio_username
ACCESS_PASSWORD=your_minio_password
```

`API_KEY` is your Finnhub API key. `ACCESS_KEY` and `ACCESS_PASSWORD` are credentials you choose for the MinIO object store - they can be any string but must be at least 3 characters.

Start the full pipeline:

```bash
docker compose up -d
```

## Predict

```bash
curl -X POST http://localhost:3001/predict \
  -H "Content-Type: application/json" \
  -d '{"current_price": 78000, "high_price": 79000, "low_price": 77000, "open_price": 78500, "previous_close": 78200, "change_pct": 0.3}'
```

Response:
```json
{"prediction": 1, "probability": {"0": 0.4, "1": 0.6}, "model_version": "5"}
```

`prediction` 1 means price goes up, 0 means price goes down. `model_version` tells you which registered MLflow version served the prediction.

## UIs

MLflow experiment tracking and model registry: `http://localhost:5000`

MinIO object store console (model artifacts): `http://localhost:9001`

Log into MinIO with the `ACCESS_KEY` and `ACCESS_PASSWORD` values from your `.env` file.

## Configuration

Model hyperparameters and pipeline settings live in `configs/config.yaml`:

```yaml
model:
  grace_period: 10        # events between model split attempts
stream:
  trigger_frequency: 10   # serialize model to MLflow every N events
  kafka_topic: stock-recommendations
```

`grace_period` and `trigger_frequency` are both set to 10 - they match intentionally. The model considers splitting every 10 events and a new version is serialized every 10 events, capturing each potential boundary change. In production this would be set higher (e.g. 200) to reduce serialization overhead

## CI/CD

On every push to `main`, GitHub Actions runs unit tests, builds and pushes three Docker images to Docker Hub (`ml-ops-ingest`, `ml-ops-train`, `ml-ops-serve`), and deploys to the Azure VM if the `DEPLOY_ENABLED` repository variable is set to `true`.

Required GitHub repository secrets:
- `DOCKER_USERNAME` and `DOCKER_PASSWORD` - Docker Hub credentials for pushing images
- `VM_SSH_PRIVATE_KEY` - private SSH key for connecting to the Azure VM
- `VM_PUBLIC_IP` - public IP address of the Azure VM

Required GitHub repository variable:
- `DEPLOY_ENABLED` - set to `true` when the VM is running, `false` otherwise

## Deploy to Azure

Provision infrastructure with Terraform (Ubuntu VM, networking, firewall rules):

```bash
cd terraform
terraform apply
```

Terraform requires a `terraform/terraform.tfvars` file (not committed to git):

```
subscription_id = "your-azure-subscription-id"
ssh_public_key  = "ssh-rsa AAAA..."
```

SSH into the VM after provisioning:

```bash
ssh -i ~/.ssh/mlops_azure adminuser@<public_ip>
```

Fix folder ownership, create `.env`, and start the stack:

```bash
sudo chown -R adminuser:adminuser /home/adminuser/app
nano /home/adminuser/app/.env
cd /home/adminuser/app && docker compose up -d
```

Access services via the VM public IP:
- API: `http://<public_ip>:3001`
- MLflow: `http://<public_ip>:5000`
- MinIO: `http://<public_ip>:9001`

Stop the VM when not in use to avoid Azure charges (deallocate, not just stop). Destroy all resources when the project is submitted:

```bash
terraform destroy
```