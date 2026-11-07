
import requests

API_URL = "https://dummyjson.com/carts"

try:
    response = requests.get(
        API_URL,
        params={
            "limit": 10,
            "skip": 0
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    carts = data["carts"]

    print("Ecommerce API connection successful!")
    print("Total carts available:", data["total"])
    print("Carts received:", len(carts))

    print("\nFirst cart details:")

    if carts:
        cart = carts[0]

        print("Cart ID:", cart["id"])
        print("Customer ID:", cart["userId"])
        print("Total amount:", cart["total"])
        print("Products:")

        for product in cart["products"]:
            print(
                product["title"],
                "| Quantity:", product["quantity"],
                "| Price:", product["price"]
            )

except requests.exceptions.RequestException as error:
    print("API request failed:", error)

except (KeyError, ValueError) as error:
    print("Unexpected API response:", error)
