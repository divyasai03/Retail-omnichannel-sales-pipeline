
import pandas as pd
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Input and output directories
BRONZE_FILE = BASE_DIR / "data" / "bronze" / "api_retail_orders.csv"
SILVER_DIR = BASE_DIR / "data" / "silver"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"

SILVER_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

SILVER_FILE = SILVER_DIR / "clean_api_orders.csv"
QUARANTINE_FILE = QUARANTINE_DIR / "rejected_api_orders.csv"

print("Starting ecommerce API data-quality validation...")

# Read Bronze data
df = pd.read_csv(BRONZE_FILE)

total_records = len(df)

# Required fields
required_columns = [
    "order_id",
    "customer_id",
    "product_id",
    "product_name",
    "quantity",
    "unit_price",
    "total_amount"
]

# Identify missing values
missing_mask = df[required_columns].isnull().any(axis=1)

# Numeric validation
numeric_columns = [
    "quantity",
    "unit_price",
    "total_amount"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

numeric_invalid_mask = (
    df["quantity"].isnull()
    | df["unit_price"].isnull()
    | df["total_amount"].isnull()
    | (df["quantity"] <= 0)
    | (df["unit_price"] <= 0)
    | (df["total_amount"] <= 0)
)

# Validate product total
expected_amount = df["quantity"] * df["unit_price"]

amount_invalid_mask = (
    (df["total_amount"] - expected_amount).abs() > 0.01
)

# Identify duplicate order-item records
duplicate_mask = df.duplicated(
    subset=["order_id", "product_id"],
    keep="first"
)

# Combine all validation failures
invalid_mask = (
    missing_mask
    | numeric_invalid_mask
    | amount_invalid_mask
    | duplicate_mask
)

# Separate valid and invalid records
valid_df = df[~invalid_mask].copy()
rejected_df = df[invalid_mask].copy()

# Add rejection reasons
reasons = []

for index in df.index:

    row_reasons = []

    if missing_mask.loc[index]:
        row_reasons.append("Missing required values")

    if numeric_invalid_mask.loc[index]:
        row_reasons.append("Invalid numeric values")

    if amount_invalid_mask.loc[index]:
        row_reasons.append("Incorrect product total")

    if duplicate_mask.loc[index]:
        row_reasons.append("Duplicate order-item record")

    reasons.append("; ".join(row_reasons))

rejected_df["rejection_reason"] = [
    reasons[index] for index in rejected_df.index
]

# Save clean and rejected records
valid_df.to_csv(SILVER_FILE, index=False)
rejected_df.to_csv(QUARANTINE_FILE, index=False)

# Display results
print("\nAPI data-quality processing completed!")
print("Total records:", total_records)
print("Invalid records:", len(rejected_df))
print("Valid records:", len(valid_df))

print("\nSilver records saved:", len(valid_df))
print("Quarantine records saved:", len(rejected_df))

print("\nRejection reasons:")

if len(rejected_df) > 0:
    print(
        rejected_df[
            ["order_id", "product_id", "rejection_reason"]
        ].to_string(index=False)
    )
else:
    print("No rejected records found.")

print("\nSilver file:", SILVER_FILE)
print("Quarantine file:", QUARANTINE_FILE)
