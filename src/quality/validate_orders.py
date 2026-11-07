
import pandas as pd
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Input files
orders_path = BASE_DIR / "data" / "bronze" / "orders.csv"
customers_path = BASE_DIR / "data" / "bronze" / "customers.csv"
products_path = BASE_DIR / "data" / "bronze" / "products.csv"

# Output directories
SILVER_DIR = BASE_DIR / "data" / "silver"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

SILVER_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# Read datasets
df = pd.read_csv(orders_path)
customers = pd.read_csv(customers_path)
products = pd.read_csv(products_path)

# Required fields
required_fields = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount"
]

# Validation checks
missing_mask = df[required_fields].isnull().any(axis=1)

numeric_mask = (
    (df["quantity"] <= 0) |
    (df["unit_price"] <= 0) |
    (df["total_amount"] <= 0)
)

amount_mask = (
    df["total_amount"] !=
    df["quantity"] * df["unit_price"]
)

parsed_dates = pd.to_datetime(
    df["order_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

date_mask = parsed_dates.isnull()

customer_ids = customers["customer_id"].dropna().unique()
product_ids = products["product_id"].dropna().unique()

customer_mask = ~df["customer_id"].isin(customer_ids)
product_mask = ~df["product_id"].isin(product_ids)

# Combine validation checks
invalid_mask = (
    missing_mask |
    numeric_mask |
    amount_mask |
    date_mask |
    customer_mask |
    product_mask
)

# Separate records
invalid_records = df[invalid_mask].copy()
valid_records = df[~invalid_mask].copy()

# Add rejection reasons
def get_rejection_reason(index):
    reasons = []

    if missing_mask.loc[index]:
        reasons.append("Missing required values")

    if numeric_mask.loc[index]:
        reasons.append("Invalid numeric values")

    if amount_mask.loc[index]:
        reasons.append("Incorrect total amount")

    if date_mask.loc[index]:
        reasons.append("Invalid order date")

    if customer_mask.loc[index]:
        reasons.append("Unknown customer ID")

    if product_mask.loc[index]:
        reasons.append("Unknown product ID")

    return "; ".join(reasons)


invalid_records["rejection_reason"] = [
    get_rejection_reason(index)
    for index in invalid_records.index
]

# Deduplicate valid orders
valid_records["updated_at"] = pd.to_datetime(
    valid_records["updated_at"]
)

valid_records = valid_records.sort_values(
    by="updated_at",
    ascending=False
)

clean_orders = valid_records.drop_duplicates(
    subset=["order_id"],
    keep="first"
)

# Save Silver records
silver_path = SILVER_DIR / "clean_orders.csv"
clean_orders.to_csv(silver_path, index=False)

# Save Quarantine records
quarantine_path = QUARANTINE_DIR / "rejected_orders.csv"
invalid_records.to_csv(quarantine_path, index=False)

# Display results
print("Data quality processing completed!")
print("Total orders:", len(df))
print("Invalid orders:", len(invalid_records))
print("Valid orders before deduplication:", len(valid_records))
print("Orders after deduplication:", len(clean_orders))

print("\nSilver records saved:", len(clean_orders))
print("Quarantine records saved:", len(invalid_records))

print("\nRejection reasons:")
print(
    invalid_records[
        ["order_id", "rejection_reason"]
    ].to_string(index=False)
)
