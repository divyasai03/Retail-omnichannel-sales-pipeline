
import requests
import pandas as pd
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Ecommerce API configuration
API_URL = "https://dummyjson.com/carts"
PAGE_SIZE = 20

# Bronze directory
BRONZE_DIR = BASE_DIR / "data" / "bronze"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = BRONZE_DIR / "api_retail_orders.csv"

# Configure automatic retries
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Create HTTP session
session = requests.Session()

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

try:
    print("Starting ecommerce API ingestion...")

    all_order_items = []
    skip = 0
    total_carts = None

    # Fetch carts page by page
    while True:

        response = session.get(
            API_URL,
            params={
                "limit": PAGE_SIZE,
                "skip": skip
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Invalid API response format")

        carts = data["carts"]
        total_carts = data["total"]

        if not isinstance(carts, list):
            raise ValueError("Carts data is not a list")

        if not carts:
            break

        # Convert each cart product into a separate row
        for cart in carts:

            for product in cart["products"]:

                order_item = {
                    "order_id": cart["id"],
                    "customer_id": cart["userId"],
                    "product_id": product["id"],
                    "product_name": product["title"],
                    "quantity": product["quantity"],
                    "unit_price": product["price"],
                    "total_amount": product["total"],
                    "discount_percentage": product["discountPercentage"],
                    "discounted_total": product["discountedTotal"],
                    "cart_total": cart["total"],
                    "cart_discounted_total": cart["discountedTotal"],
                    "total_products": cart["totalProducts"],
                    "total_quantity": cart["totalQuantity"]
                }

                all_order_items.append(order_item)

        print(
            f"Fetched {len(carts)} carts "
            f"(skip={skip})"
        )

        skip += len(carts)

        if skip >= total_carts:
            break

    # Convert extracted records into DataFrame
    df = pd.DataFrame(all_order_items)

    # Save ecommerce order items into Bronze
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nEcommerce API ingestion completed!")
    print("Total carts available:", total_carts)
    print("Total order-item records:", len(df))
    print("Bronze file saved:", OUTPUT_FILE)

    print("\nFirst five order-item records:")
    print(df.head().to_string(index=False))

except requests.exceptions.RequestException as error:
    print("API connection or HTTP request failed!")
    print("Error:", error)

except (KeyError, TypeError, ValueError) as error:
    print("API response processing failed!")
    print("Error:", error)

finally:
    session.close()
