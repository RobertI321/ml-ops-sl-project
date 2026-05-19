import tempfile
import mlflow
import pickle
import os

# Extract features and label from events
def extract_features_and_label(event):
    X = {
        "current_price": event["current_price"],
        "high_price": event["high_price"],
        "low_price": event["low_price"],
        "open_price": event["open_price"],
        "previous_close": event["previous_close"],
        "change_pct": event["change_pct"]
    }
    y = event["label"]
    return X, y

# Save model to MLflow and register new version
def save_model(model, run_id, model_name, client):
    # figure out what the next version number will be
    try:
        client.create_registered_model(model_name)
    except Exception:
        pass  # already exists, ignore

    try:
        existing = client.search_model_versions(f"name='{model_name}'")
        next_version = max([int(v.version) for v in existing], default=0) + 1 if existing else 1
    except Exception:
        next_version = 1
    
    artifact_path = f"model_v{next_version}"
    
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "model.pkl")
        with open(path, "wb") as f:
            pickle.dump(model, f)
        mlflow.log_artifact(path, artifact_path=artifact_path)
    
    mv = client.create_model_version(
        name=model_name,
        source=f"runs:/{run_id}/{artifact_path}/model.pkl",
        run_id=run_id
    )
    return mv.version

def get_recommendation_trends(client, latest_t=0):

    quote = client.quote("BINANCE:BTCUSDT")

    if quote["t"] == latest_t:
        return None
    
    latest_t = quote["t"]

    return quote, latest_t

def build_event(quote, latest_c=0):
    label = 1 if quote["c"] > latest_c else 0
    event = {
        "symbol": "BINANCE:BTCUSDT",
        "timestamp": quote["t"],
        "current_price": quote["c"],
        "high_price": quote["h"],
        "low_price": quote["l"],
        "open_price": quote["o"],
        "previous_close": quote["pc"],
        "change": quote["d"],
        "change_pct": quote["dp"],
        "label": label
    }
    return event

