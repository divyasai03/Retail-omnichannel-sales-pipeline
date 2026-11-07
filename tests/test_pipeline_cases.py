import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def test_order_schema_validation():
    df = pd.read_csv(
        BASE_DIR / "data/source/csv/test_invalid_orders.csv"
    )

    required_columns = [
        "order_id", "customer_id", "product_id",
        "quantity", "unit_price", "total_amount",
        "city", "order_date", "updated_at",
        "channel", "status"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    assert len(missing) > 0


def test_invalid_amount_detection():
    df = pd.read_csv(
        BASE_DIR / "data/source/csv/test_invalid_amount.csv"
    )

    expected = df["quantity"] * df["unit_price"]
    invalid = df[df["total_amount"] != expected]

    assert len(invalid) > 0


def test_invalid_date_detection():
    df = pd.read_csv(
        BASE_DIR / "data/source/csv/test_invalid_dates.csv"
    )

    parsed = pd.to_datetime(
        df["order_date"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    assert parsed.isna().sum() > 0


def test_unknown_customer_detection():
    orders = pd.read_csv(
        BASE_DIR / "data/source/csv/test_invalid_customer.csv"
    )

    customers = pd.read_csv(
        BASE_DIR / "data/bronze/customers.csv"
    )

    valid_ids = customers["customer_id"].dropna().unique()
    invalid = orders[~orders["customer_id"].isin(valid_ids)]

    assert len(invalid) > 0


def test_unknown_product_detection():
    orders = pd.read_csv(
        BASE_DIR / "data/source/csv/test_invalid_product.csv"
    )

    products = pd.read_csv(
        BASE_DIR / "data/bronze/products.csv"
    )

    valid_ids = products["product_id"].dropna().unique()
    invalid = orders[~orders["product_id"].isin(valid_ids)]

    assert len(invalid) > 0


def test_clean_orders_have_no_duplicate_ids():
    df = pd.read_csv(
        BASE_DIR / "data/silver/clean_orders.csv"
    )

    assert not df["order_id"].duplicated().any()


def test_unified_orders_have_unique_business_keys():
    df = pd.read_csv(
        BASE_DIR / "data/silver/unified_orders.csv"
    )

    business_key = [
        "source_system", "order_id", "product_id"
    ]

    assert not df.duplicated(subset=business_key).any()
    assert len(df) > 0