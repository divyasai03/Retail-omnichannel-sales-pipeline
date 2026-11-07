
import pandas as pd

# Read test CSV
df = pd.read_csv("data/source/csv/test_invalid_dates.csv")

# Convert order_date into a date
df["parsed_date"] = pd.to_datetime(
    df["order_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

# Identify invalid dates
invalid_dates = df[df["parsed_date"].isnull()]

# Identify valid dates
valid_dates = df[df["parsed_date"].notnull()]

# Display results
print("Total test records:", len(df))
print("Valid dates:", len(valid_dates))
print("Invalid dates:", len(invalid_dates))

print("\nInvalid date records:")
print(
    invalid_dates[["order_id", "order_date"]].to_string(index=False)
)
