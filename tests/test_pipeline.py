import sys
sys.path.insert(0, './src')

from utilis import extract_features_and_label, build_event


fake_event = {
    "current_price": 78000,
    "high_price": 79000,
    "low_price": 77000,
    "open_price": 78500,
    "previous_close": 78200,
    "change_pct": 0.3,
    "label": 1
}

fake_quote = {
        "c": 78000,
        "h": 79000,
        "l": 77000,
        "o": 78500,
        "pc": 78200,
        "d": 200,
        "dp": 0.3,
        "t": 1234567890
    }

def test_build_event():
    event = build_event(fake_quote, latest_c=78200)
    assert event["current_price"] == 78000
    assert event["high_price"] == 79000
    assert event["low_price"] == 77000
    assert event["open_price"] == 78500
    assert event["previous_close"] == 78200
    assert event["change"] == 200
    assert event["change_pct"] == 0.3
    assert event["label"] == 0  # since current_price 78000 < latest_c 78200

def test_extract_features_and_label():
    X, y = extract_features_and_label(fake_event)
    assert X["current_price"] == 78000
    assert X["high_price"] == 79000
    assert X["low_price"] == 77000
    assert X["open_price"] == 78500
    assert X["previous_close"] == 78200
    assert X["change_pct"] == 0.3
    assert "label" not in X
    assert y == 1
