
import pandas as pd
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Bronze input files
BRONZE_DIR = BASE_DIR / "data" / "bronze"

ORDERS_FILE = BRONZE_DIR / "postgres_orders.csv"
CUSTOMERS_FILE = BRONZE_DIR / "postgres_customers.csv"
PRODUCTS_FILE = BRONZE_DIR / "postgres_products.csv"

# Silver and Quarantine directories
SILVER_DIR = BASE_DIR / "data" / "silver"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

SILVER_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

SILVER_FILE = SILVER_DIR / "clean_postgres_orders.csv"
QUARANTINE_FILE = QUARANTINE_DIR / "rejected_postgres_orders.csv"

print("Starting PostgreSQL data-quality validation...")

# Read Bronze datasets
df = pd.read_csv(ORDERS_FILE)
customers = pd.read_csv(CUSTOMERS_FILE)
products = pd.read_csv(PRODUCTS_FILE)

total_records = len(df)

# Required fields
required_columns = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_date"
]

# Check missing values
missing_mask = df[required_columns].isnull().any(axis=1)

# Convert numeric columns
numeric_columns = ["quantity", "unit_price", "total_amount"]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Check numeric values
numeric_invalid_mask = (
    df["quantity"].isnull()
    | df["unit_price"].isnull()
    | df["total_amount"].isnull()
    | (df["quantity"] <= 0)
    | (df["unit_price"] <= 0)
    | (df["total_amount"] <= 0)
)

# Check total amount
expected_amount = df["quantity"] * df["unit_price"]

amount_invalid_mask = (
    (df["total_amount"] - expected_amount).abs() > 0.01
)

# Validate order dates
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
)

date_invalid_mask = df["order_date"].isnull()

# Validate customer references
valid_customers = set(customers["customer_id"].dropna())

customer_invalid_mask = ~df["customer_id"].isin(valid_customers)

# Validate product references
valid_products = set(products["product_id"].dropna())

product_invalid_mask = ~df["product_id"].isin(valid_products)

# Check duplicate order IDs
duplicate_mask = df.duplicated(
    subset=["order_id"],
    keep="first"
)

# Combine all validation rules
invalid_mask = (
    missing_mask
    | numeric_invalid_mask
    | amount_invalid_mask
    | date_invalid_mask
    | customer_invalid_mask
    | product_invalid_mask
    | duplicate_mask
)

# Separate valid and invalid records
valid_df = df[~invalid_mask].copy()
rejected_df = df[invalid_mask].copy()

# Generate rejection reasons
reasons = []

for index in df.index:

    row_reasons = []

    if missing_mask.loc[index]:
        row_reasons.append("Missing required values")

    if numeric_invalid_mask.loc[index]:
        row_reasons.append("Invalid numeric values")

    if amount_invalid_mask.loc[index]:
        row_reasons.append("Incorrect total amount")

    if date_invalid_mask.loc[index]:
        row_reasons.append("Invalid order date")

    if customer_invalid_mask.loc[index]:
        row_reasons.append("Unknown customer ID")

    if product_invalid_mask.loc[index]:
        row_reasons.append("Unknown product ID")

    if duplicate_mask.loc[index]:
        row_reasons.append("Duplicate order ID")

    reasons.append("; ".join(row_reasons))

rejected_df["rejection_reason"] = [
    reasons[index] for index in rejected_df.index
]

# Save Silver and Quarantine files
valid_df.to_csv(SILVER_FILE, index=False)
rejected_df.to_csv(QUARANTINE_FILE, index=False)

# Display results
print("\nPostgreSQL data-quality processing completed!")
print("Total records:", total_records)
print("Invalid records:", len(rejected_df))
print("Valid records:", len(valid_df))

print("\nSilver records saved:", len(valid_df))
print("Quarantine records saved:", len(rejected_df))

print("\nRejection reasons:")

if len(rejected_df) > 0:
    print(
        rejected_df[
            ["order_id", "rejection_reason"]
        ].to_string(index=False)
    )
else:
    print("No rejected records found.")

print("\nSilver file:", SILVER_FILE)
print("Quarantine file:", QUARANTINE_FILE)