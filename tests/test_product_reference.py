
import pandas as pd

# Read test order
orders = pd.read_csv(
    "data/source/csv/test_invalid_product.csv"
)

# Read existing products
products = pd.read_csv(
    "data/bronze/products.csv"
)

# Get valid product IDs
product_ids = products["product_id"].dropna().unique()

# Find orders with unknown products
invalid_orders = orders[
    ~orders["product_id"].isin(product_ids)
]

# Display result
if invalid_orders.empty:
    print("PASS: All product references are valid!")
else:
    print("FAIL: Unknown product references found!")
    print(
        invalid_orders[
            ["order_id", "product_id"]
        ].to_string(index=False)
    )