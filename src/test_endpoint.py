
import requests

response = requests.post("http://localhost:3001/predict", json={
    "current_price": 78000,
    "high_price": 79000,
    "low_price": 77000,
    "open_price": 78500,
    "previous_close": 78200,
    "change_pct": 0.3
})

print(response.json())