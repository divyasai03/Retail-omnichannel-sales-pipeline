
import pandas as pd

# Required columns for orders
required_columns = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "city",
    "order_date",
    "updated_at",
    "channel",
    "status"
]

# Read the intentionally incomplete CSV
df = pd.read_csv("data/source/csv/test_invalid_orders.csv")

# Identify missing columns
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

# Display validation result
if missing_columns:
    print("Schema validation failed!")
    print("Missing columns:", missing_columns)
else:
    print("Schema validation passed!")
