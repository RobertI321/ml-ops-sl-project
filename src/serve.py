from flask import Flask, jsonify, request
from mlflow import MlflowClient
import pickle
import mlflow
import time
import threading
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

mlflow_config = config["mlflow"]

client = MlflowClient()

current_model = None
current_version = None

def refresh_model():
    global current_model, current_version
    while True:
        try:
            mv = client.get_model_version_by_alias(
                name=mlflow_config["model_name"],
                alias="Production"
            )
            if mv.version != current_version:
                print(f"New model version detected: {mv.version}")
                path = mlflow.artifacts.download_artifacts(
                    f"runs:/{mv.run_id}/model_v{mv.version}/model.pkl"
                )
                with open(path, "rb") as f:
                    current_model = pickle.load(f)
                current_version = mv.version
                print(f"Swapped to model version {current_version}")
        except Exception as e:
            print(f"Model refresh failed: {e}")
        
        time.sleep(60)  # check every 60 seconds

# start the background thread before Flask
thread = threading.Thread(target=refresh_model, daemon=True)
thread.start()

def extract_features_and_label(event):
    X = {
        "current_price": event["current_price"],
        "high_price": event["high_price"],
        "low_price": event["low_price"],
        "open_price": event["open_price"],
        "previous_close": event["previous_close"],
        "change_pct": event["change_pct"]
    }
    return X

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "BTC Price Prediction API!"

@app.route('/predict', methods=['POST'])
def predict():
    if current_model is None:
        return jsonify({"error": "Model not loaded yet"}), 503
    
    data = request.json
    X = extract_features_and_label(data)
    
    y_pred = current_model.predict_proba_one(X)
    y_pred_class = current_model.predict_one(X)
    
    return jsonify({
        "prediction": int(y_pred_class),
        "probability": y_pred,
        "model_version": current_version
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
