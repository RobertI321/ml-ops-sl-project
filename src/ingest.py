import finnhub
import time
#import requests
import os
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


def get_recommendation_trends(client, latest_t=0, trends = None):
    quote = client.quote("NVDA")
    rec_trends = trends

    if quote["t"] == latest_t:
        print("No new data available.")
        return None
    latest_t = quote["t"]

    return quote, rec_trends, latest_t

def build_event(quote, rec_trends, latest_c=0):
    label = 1 if quote["c"] > latest_c else 0
    event = {
        "symbol": "NVDA",
        "timestamp": quote["t"],
        "current_price": quote["c"],
        "high_price": quote["h"],
        "low_price": quote["l"],
        "open_price": quote["o"],
        "previous_c": quote["pc"],
        "buy" : rec_trends[0]['buy'],
        "hold" : rec_trends[0]['hold'],
        "sell" : rec_trends[0]['sell'],
        "strong_buy" : rec_trends[0]['strongBuy'],
        "strong_sell" : rec_trends[0]['strongSell'],
        "label": label
    }
    return event

# quote, rec, latest_t = get_recommendation_trends(finnhub_client)
# event = build_event(quote, rec, quote["pc"])
# print("\n", quote)
# print("\n", rec)
# print("\n", latest_t)
# print("\n", event)


def main():
    finnhub_client = finnhub.Client(api_key=os.getenv("API_KEY"))
    rec_trends = finnhub_client.recommendation_trends('NVDA')
    latest_t = 0
    latest_c = 0  # track across iterations
    while True:
        result = get_recommendation_trends(finnhub_client, latest_t, rec_trends)
        if result is not None:
            quote, rec_trends, latest_t = result
            event = build_event(quote, rec_trends, latest_c)  # pass it in
            latest_c = quote["c"]  # update after building event

            print("\n", event)
            time.sleep(30)  # Wait 30 seconds before the next iteration
            continue
        else:
            print("No new data. Waiting for the next check.")
            time.sleep(60*60*17.5)  # Check for new data every 17.5 hours (after market close)

if __name__ == "__main__":
    main()