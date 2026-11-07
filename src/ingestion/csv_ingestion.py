
import pandas as pd
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Source and Bronze directories
SOURCE_DIR = BASE_DIR / "data" / "source" / "csv"
BRONZE_DIR = BASE_DIR / "data" / "bronze"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# Required columns for each dataset
required_columns = {
    "orders": [
        "order_id", "customer_id", "product_id",
        "quantity", "unit_price", "total_amount",
        "city", "order_date", "updated_at",
        "channel", "status"
    ],
    "customers": [
        "customer_id", "customer_name",
        "email", "city", "updated_at"
    ],
    "products": [
        "product_id", "product_name",
        "category", "brand", "unit_price", "updated_at"
    ]
}

files = {
    "orders": "orders.csv",
    "customers": "customers.csv",
    "products": "products.csv"
}

print("Starting CSV ingestion with schema validation...")

for dataset_name, file_name in files.items():

    source_path = SOURCE_DIR / file_name
    bronze_path = BRONZE_DIR / file_name

    # Read CSV
    df = pd.read_csv(source_path)

    # Check required columns
    missing_columns = [
        column for column in required_columns[dataset_name]
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing columns: {missing_columns}"
        )

    print(f"{dataset_name}: Schema validation passed")

    # Save data into Bronze
    df.to_csv(bronze_path, index=False)

    print(f"{dataset_name}: {len(df)} records ingested successfully")

print("CSV ingestion completed successfully!")
