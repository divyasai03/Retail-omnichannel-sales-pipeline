
# =========================================================
# RETAIL OMNICHANNEL CAPSTONE
# Load Date Dimension and Sales Fact Table
# =========================================================

from pathlib import Path
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "retail_omnichannel_db")
)

engine = create_engine(db_url)

UNIFIED_FILE = BASE_DIR / "data" / "silver" / "unified_orders.csv"


def clean_value(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


# ---------------------------------------------------------
# 2. LOAD UNIFIED SALES DATA
# ---------------------------------------------------------

def read_sales_data():

    if not UNIFIED_FILE.exists():
        raise FileNotFoundError(
            f"Unified orders file not found: {UNIFIED_FILE}"
        )

    df = pd.read_csv(UNIFIED_FILE)

    required = [
        "source_system", "order_id", "customer_id",
        "product_id", "quantity", "unit_price",
        "total_amount", "order_date", "updated_at"
    ]

    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


# ---------------------------------------------------------
# 3. LOAD DATE DIMENSION
# ---------------------------------------------------------

def load_date_dimension(conn, df):

    dates = pd.to_datetime(df["order_date"], errors="coerce").dropna()
    unique_dates = sorted(dates.dt.date.unique())

    inserted = 0

    for current_date in unique_dates:

        date_key = int(current_date.strftime("%Y%m%d"))

        result = conn.execute(
            text("""
                INSERT INTO dim_date (
                    date_key, full_date, day_number,
                    month_number, month_name,
                    quarter_number, year_number, day_name
                )
                VALUES (
                    :date_key, :full_date, :day_number,
                    :month_number, :month_name,
                    :quarter_number, :year_number, :day_name
                )
                ON CONFLICT (date_key) DO NOTHING
            """),
            {
                "date_key": date_key,
                "full_date": current_date,
                "day_number": current_date.day,
                "month_number": current_date.month,
                "month_name": current_date.strftime("%B"),
                "quarter_number": (current_date.month - 1) // 3 + 1,
                "year_number": current_date.year,
                "day_name": current_date.strftime("%A")
            }
        )

        inserted += result.rowcount

    return inserted


# ---------------------------------------------------------
# 4. FIND CUSTOMER SURROGATE KEY
# ---------------------------------------------------------

def find_customer_key(conn, source, customer_id, updated_at):

    if updated_at is None:
        return conn.execute(
            text("""
                SELECT customer_key
                FROM dim_customer
                WHERE source_system = :source
                  AND customer_id = :customer_id
                  AND is_current = TRUE
            """),
            {
                "source": source,
                "customer_id": customer_id
            }
        ).scalar()

    return conn.execute(
        text("""
            SELECT customer_key
            FROM dim_customer
            WHERE source_system = :source
              AND customer_id = :customer_id
              AND effective_start_date <= :as_of
              AND (
                    effective_end_date IS NULL
                    OR effective_end_date > :as_of
              )
            ORDER BY effective_start_date DESC
            LIMIT 1
        """),
        {
            "source": source,
            "customer_id": customer_id,
            "as_of": updated_at
        }
    ).scalar()


# ---------------------------------------------------------
# 5. FIND PRODUCT SURROGATE KEY
# ---------------------------------------------------------

def find_product_key(conn, source, product_id):

    return conn.execute(
        text("""
            SELECT product_key
            FROM dim_product
            WHERE source_system = :source
              AND product_id = :product_id
        """),
        {
            "source": source,
            "product_id": product_id
        }
    ).scalar()


# ---------------------------------------------------------
# 6. LOAD SALES FACT TABLE
# ---------------------------------------------------------

def load_fact_sales(conn, df):

    inserted = 0
    skipped = 0
    missing_dimension = 0

    for _, row in df.iterrows():

        source = clean_value(row["source_system"])
        order_id = clean_value(row["order_id"])
        customer_id = clean_value(row["customer_id"])
        product_id = clean_value(row["product_id"])

        if not all([source, order_id, customer_id, product_id]):
            skipped += 1
            continue

        updated_at = pd.to_datetime(
            row["updated_at"], errors="coerce"
        )

        if pd.isna(updated_at):
            updated_at = None
        else:
            updated_at = updated_at.to_pydatetime()

        customer_key = find_customer_key(
            conn, source, customer_id, updated_at
        )

        product_key = find_product_key(
            conn, source, product_id
        )

        if customer_key is None or product_key is None:
            missing_dimension += 1
            continue

        order_date = pd.to_datetime(
            row["order_date"], errors="coerce"
        )

        date_key = None

        if not pd.isna(order_date):
            date_key = int(order_date.strftime("%Y%m%d"))

        quantity = int(row["quantity"])
        unit_price = float(row["unit_price"])
        total_amount = float(row["total_amount"])

        result = conn.execute(
            text("""
                INSERT INTO fact_sales (
                    source_system, order_id, product_id,
                    customer_key, product_key, date_key,
                    quantity, unit_price, total_amount,
                    channel, status
                )
                VALUES (
                    :source, :order_id, :product_id,
                    :customer_key, :product_key, :date_key,
                    :quantity, :unit_price, :total_amount,
                    :channel, :status
                )
                ON CONFLICT (
                    source_system, order_id, product_id
                ) DO NOTHING
                RETURNING sales_key
            """),
            {
                "source": source,
                "order_id": order_id,
                "product_id": product_id,
                "customer_key": customer_key,
                "product_key": product_key,
                "date_key": date_key,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "channel": clean_value(row["channel"]),
                "status": clean_value(row["status"])
            }
        )

        if result.scalar() is not None:
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped, missing_dimension


# ---------------------------------------------------------
# 7. MAIN EXECUTION
# ---------------------------------------------------------

def main():

    print("Starting Gold warehouse loading...")

    df = read_sales_data()

    print(f"Unified records received: {len(df)}")

    with engine.begin() as conn:

        date_inserted = load_date_dimension(conn, df)

        fact_inserted, skipped, missing = load_fact_sales(
            conn, df
        )

        date_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_date")
        ).scalar()

        fact_count = conn.execute(
            text("SELECT COUNT(*) FROM fact_sales")
        ).scalar()

        total_sales = conn.execute(
            text("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM fact_sales
            """)
        ).scalar()

    print("\nGold warehouse loading completed!")
    print("----------------------------------")
    print(f"Date records inserted: {date_inserted}")
    print(f"Total date records: {date_count}")
    print(f"Fact records inserted: {fact_inserted}")
    print(f"Fact records skipped: {skipped}")
    print(f"Missing dimension records: {missing}")
    print(f"Total fact records: {fact_count}")
    print(f"Total sales amount: {total_sales}")
    print("----------------------------------")


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
