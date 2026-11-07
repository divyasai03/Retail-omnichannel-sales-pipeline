
import requests
import json

API_URL = "https://dummyjson.com/carts/1"

response = requests.get(
    API_URL,
    timeout=30
)

response.raise_for_status()

cart = response.json()

print("Complete cart response structure:")
print(json.dumps(cart, indent=4))
