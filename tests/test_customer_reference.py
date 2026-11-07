
import pandas as pd

# Read test order
orders = pd.read_csv(
    "data/source/csv/test_invalid_customer.csv"
)

# Read existing customers
customers = pd.read_csv(
    "data/bronze/customers.csv"
)

# Get valid customer IDs
customer_ids = customers["customer_id"].dropna().unique()

# Find orders with unknown customers
invalid_orders = orders[
    ~orders["customer_id"].isin(customer_ids)
]

# Display result
if invalid_orders.empty:
    print("PASS: All customer references are valid!")
else:
    print("FAIL: Unknown customer references found!")
    print(
        invalid_orders[
            ["order_id", "customer_id"]
        ].to_string(index=False)
    )
