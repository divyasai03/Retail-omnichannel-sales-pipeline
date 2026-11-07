
import pandas as pd

# Read the test CSV
df = pd.read_csv("data/source/csv/test_invalid_amount.csv")

# Calculate expected total
expected_amount = df["quantity"] * df["unit_price"]

# Find incorrect amounts
invalid_amounts = df[
    df["total_amount"] != expected_amount
]

# Display result
if invalid_amounts.empty:
    print("PASS: All order amounts are correct!")
else:
    print("FAIL: Incorrect order amounts found!")
    print(invalid_amounts.to_string(index=False))
