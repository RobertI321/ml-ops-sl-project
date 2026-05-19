from river import tree, metrics, drift
from kafka import KafkaConsumer
import json
import mlflow
from mlflow import MlflowClient
import yaml
import pickle
import tempfile
import os

from utils import extract_features_and_label

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

def load_latest_model(model_name, client):
    try:
        mv = client.get_model_version_by_alias(
            name=model_name,
            alias="Production"
        )
        path = mlflow.artifacts.download_artifacts(
            run_id=mv.run_id,
            artifact_path=f"model_v{mv.version}"
        )
        with open(os.path.join(path, "model.pkl"), "rb") as f:
            model = pickle.load(f)
        print(f"Loaded existing model version {mv.version}")
        return model
    except Exception as e:
        print(f"No existing model found, starting fresh: {e}")
        return None
    
def main():

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    model_config = config["model"]
    mlflow_config = config["mlflow"]

    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])
    client = MlflowClient()

    # Model update period (number of events before model update)
    GRACE_PERIOD = config["model"]["grace_period"]
    TRIGGER_FREQUENCY = GRACE_PERIOD  
    # Kafka consumer setup
    consumer = KafkaConsumer(
        'stock-recommendations',
        group_id = "stock-recommendation-group",
        bootstrap_servers='kafka:9092',
        auto_offset_reset='latest', # Start consuming from the latest messages (new events) when the consumer starts
        enable_auto_commit=True, # Save progress automatically
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    with mlflow.start_run():
        mlflow.log_param("model", "HoeffdingAdaptiveTreeClassifier")
        mlflow.log_params(model_config)
        mlflow.set_tag("stage", "Production") 

        # try to load existing model (when container restarts), fall back to fresh
        print("Trying to load existing model...")
        existing = load_latest_model(mlflow_config["model_name"], client)
        model = existing if existing is not None else tree.HoeffdingAdaptiveTreeClassifier(**model_config)

        #Using AUC as the evaluation metric
        metric = metrics.ROCAUC()
        
        # Concept Drift Detection
        drift_detector  = drift.ADWIN()
        try:
            for message in consumer:

                print(f'Received message from Kafka: KEY = {message.key}, PARTITION = {message.partition}, OFFSET = {message.offset}')
                event = message.value
                print(f"Received event: {event}")

                # Get features and label
                X, y = extract_features_and_label(event)

                # Predict and update metric
                y_pred = model.predict_proba_one(X)
                y_pred_class = model.predict_one(X)
                metric.update(y, y_pred)
                model.learn_one(X, y)
                
                # Update drift detector the error (1 if prediction is wrong, 0 if correct); detects when model starts making more errors than expected
                error = 1 if y_pred_class != y else 0
                drift_detector.update(error)

                # Log AUC metric to MLflow
                mlflow.log_metric("AUC", metric.get(), step=message.offset)

                print(f"Processed event at timestamp {event['timestamp']}, AUC: {metric.get():.4f}, true label: {y}, predicted probabilities: {y_pred}, predicted class: {y_pred_class}")

                # Check for concept drift
                if drift_detector.drift_detected:
                    mlflow.log_metric("drift_detected", 1, step=message.offset)
                else:
                    mlflow.log_metric("drift_detected", 0, step=message.offset)
                
                # Save model periodically based the kafka message offset. This ensures we save the model after processing a certain number of events, regardless of how fast they arrive. We also check that the offset is greater than 0 to avoid saving an untrained model at the very beginning.
                if message.offset % TRIGGER_FREQUENCY == 0 and message.offset > 0:
                    print(f"Saving model version at event {message.offset}")
                    save_model(model, mlflow.active_run().info.run_id, mlflow_config["model_name"], client)

                    versions = client.get_latest_versions(name=mlflow_config["model_name"])
                    latest_version = max(versions, key=lambda v: int(v.version)).version
                    client.set_registered_model_alias(
                    name=mlflow_config["model_name"],
                    version=latest_version,
                    alias="Production",                    
                    )
                    print(f"Model version {latest_version} set as Production")

        except KeyboardInterrupt:
            print("Stopping consumer...")
        
        finally:
            consumer.close()

if __name__ == "__main__":
    main()