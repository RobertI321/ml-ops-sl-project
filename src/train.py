from river import tree, metrics, drift
from kafka import KafkaConsumer
import json
import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("experiment-1")

GRACE_PERIOD = 200 # Model update period (number of events before model update)
TRIGGER_FREQUENCY = GRACE_PERIOD  # 

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


def main():

    # Kafka consumer setup
    consumer = KafkaConsumer(
        'stock-recommendations',
        group_id = "stock-recommendation-group",
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True, # Save progress automatically
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    # Models and metrics
    model = tree.HoeffdingTreeClassifier(grace_period=GRACE_PERIOD)
    metric = metrics.ROCAUC()  # Using AUC as the evaluation metric

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
            metric.update(y, y_pred)
            model.learn_one(X, y)
            
            # Update drift detector with the true label
            drift_detector.update(y)

            # Log AUC metric to MLflow
            mlflow.log_metric("AUC", metric.get(), step=message.offset)

            print(f"Processed event at timestamp {event['timestamp']}, AUC: {metric.get():.4f}, true label: {y}, predicted probabilities: {y_pred}")

            # Check for concept drift
            if drift_detector.change_detected:
                print(f'Drift detected at offset {message.offset}')
                mlflow.set_tag("drift_detected", "True")

    except KeyboardInterrupt:
        print("Stopping consumer...")
    
    finally:
        consumer.close()

if __name__ == "__main__":
    main()