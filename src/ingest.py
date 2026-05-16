import finnhub
import time
from kafka import KafkaProducer
import json
import os
from finnhub.exceptions import FinnhubAPIException

from dotenv import load_dotenv
load_dotenv()

# Client
#finnhub_client = finnhub.Client(api_key=os.getenv("API_KEY"))

# # Stock candles
# quote = finnhub_client.quote("NVDA")
# print("\n",quote)

# # Recommendation trends
# rec_trends = finnhub_client.recommendation_trends('NVDA')
# print("\n",rec_trends)


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

def on_send_success(record_metadata):
    print(f"Message sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")

def on_send_error(excp):
    print('Failed to send message', exc_info=excp)

# quote, rec, latest_t = get_recommendation_trends(finnhub_client)
# event = build_event(quote, rec, quote["pc"])
# print("\n", quote)
# print("\n", rec)
# print("\n", latest_t)
# print("\n", event)


def main():
    finnhub_client = finnhub.Client(api_key=os.getenv("API_KEY"))
    latest_t = 0
    latest_c = 0  # track across iterations

    # Kafka producer setup
    producer = KafkaProducer(bootstrap_servers="kafka:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    while True:
        try:
            result = get_recommendation_trends(finnhub_client, latest_t)

            if result is not None:
                quote, latest_t = result
                event = build_event(quote, latest_c)
                latest_c = quote["c"]
                print(event)
                producer.send("stock-recommendations", event).add_callback(on_send_success).add_errback(on_send_error)
                producer.flush()

        except FinnhubAPIException as e:
            if e.status_code == 429:
                print("Rate limit hit, waiting 60s...")
                time.sleep(60)
            else:
                print(f"API error: {e}")

        except Exception as e:
            print(f"Unexpected error: {e}")

        time.sleep(30)  # single sleep, always, end of loop
if __name__ == "__main__":
    main()