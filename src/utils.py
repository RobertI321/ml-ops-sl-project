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

