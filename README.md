# Stream Learning MLOps Pipeline

A production-grade MLOps pipeline for real-time BTC price direction prediction using Stream Learning.

## Quick Start

```bash
docker compose up -d
```

## Test the API

```bash
curl -X POST http://localhost:3001/predict \
  -H "Content-Type: application/json" \
  -d '{"current_price": 78000, "high_price": 79000, "low_price": 77000, "open_price": 78500, "previous_close": 78200, "change_pct": 0.3}'
```

## Services

- **MLflow UI** — http://localhost:5000
- **MinIO Console** — http://localhost:9001
- **API** — http://localhost:3001