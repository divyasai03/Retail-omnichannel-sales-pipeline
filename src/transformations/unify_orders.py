
import pandas as pd
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parents[2]

SILVER_DIR = BASE_DIR / "data" / "silver"
BRONZE_DIR = BASE_DIR / "data" / "bronze"

# Read the three clean datasets
csv_orders = pd.read_csv(SILVER_DIR / "clean_orders.csv")
api_orders = pd.read_csv(SILVER_DIR / "clean_api_orders.csv")
postgres_orders = pd.read_csv(
    SILVER_DIR / "clean_postgres_orders.csv"
)

# Read product reference data to obtain product names
csv_products = pd.read_csv(BRONZE_DIR / "products.csv")
postgres_products = pd.read_csv(
    BRONZE_DIR / "postgres_products.csv"
)

# Build product name mappings
csv_product_names = dict(
    zip(csv_products["product_id"], csv_products["product_name"])
)

postgres_product_names = dict(
    zip(
        postgres_products["product_id"],
        postgres_products["product_name"]
    )
)

# Add product names to CSV orders
csv_orders["product_name"] = csv_orders["product_id"].map(
    csv_product_names
)

# Add product names to PostgreSQL orders
postgres_orders["product_name"] = postgres_orders["product_id"].map(
    postgres_product_names
)

# Identify the source of each dataset
csv_orders["source_system"] = "CSV"
api_orders["source_system"] = "REST_API"
postgres_orders["source_system"] = "POSTGRESQL"

# Define the common structure
common_columns = [
    "source_system",
    "order_id",
    "customer_id",
    "product_id",
    "product_name",
    "quantity",
    "unit_price",
    "total_amount",
    "order_date",
    "updated_at",
    "channel",
    "status"
]

# Add any missing common columns
for df in [csv_orders, api_orders, postgres_orders]:
    for column in common_columns:
        if column not in df.columns:
            df[column] = pd.NA

# Keep only the common columns in the same order
csv_orders = csv_orders[common_columns]
api_orders = api_orders[common_columns]
postgres_orders = postgres_orders[common_columns]

# Combine all three sources
unified_orders = pd.concat(
    [csv_orders, api_orders, postgres_orders],
    ignore_index=True
)

# Save unified Silver dataset
output_file = SILVER_DIR / "unified_orders.csv"

unified_orders.to_csv(output_file, index=False)

# Display results
print("Multi-source integration completed!")

print("\nSource record counts:")
print("CSV orders:", len(csv_orders))
print("REST API order items:", len(api_orders))
print("PostgreSQL orders:", len(postgres_orders))

print("\nTotal unified records:", len(unified_orders))

print("\nRecords by source:")
print(unified_orders["source_system"].value_counts())

print("\nUnified dataset columns:")
print(list(unified_orders.columns))

print("\nFirst five unified records:")
print(unified_orders.head().to_string(index=False))

print("\nUnified Silver file saved:", output_file)
