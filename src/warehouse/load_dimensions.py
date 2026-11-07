
# =========================================================
# RETAIL OMNICHANNEL CAPSTONE
# Load Customer and Product Dimensions
# Includes SCD Type 2 customer history
# =========================================================

from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ---------------------------------------------------------
# 1. PROJECT CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=__import__("os").getenv("DB_PASSWORD"),
    host="localhost",
    port=5432,
    database="retail_omnichannel_db"
)

engine = create_engine(db_url)

BRONZE = BASE_DIR / "data" / "bronze"

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------

def clean_value(value):
    if pd.isna(value):
        return None
    return str(value).strip()


def get_timestamp(value):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.Timestamp("1900-01-01").to_pydatetime()
    return parsed.to_pydatetime()


# ---------------------------------------------------------
# 3. LOAD CUSTOMER SOURCE DATA
# ---------------------------------------------------------

def load_customer_sources():

    customers = []

    # CSV customers
    csv_file = BRONZE / "customers.csv"

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        for _, row in df.iterrows():
            customers.append({
                "source_system": "CSV",
                "customer_id": clean_value(row["customer_id"]),
                "customer_name": clean_value(row["customer_name"]),
                "email": clean_value(row["email"]),
                "city": clean_value(row["city"]),
                "updated_at": get_timestamp(row["updated_at"])
            })

    # PostgreSQL customers
    pg_file = BRONZE / "postgres_customers.csv"

    if pg_file.exists():
        df = pd.read_csv(pg_file)

        for _, row in df.iterrows():
            customers.append({
                "source_system": "POSTGRESQL",
                "customer_id": clean_value(row["customer_id"]),
                "customer_name": clean_value(row["customer_name"]),
                "email": clean_value(row["email"]),
                "city": clean_value(row["city"]),
                "updated_at": get_timestamp(row["updated_at"])
            })

    # REST API customers
    api_file = BRONZE / "api_retail_orders.csv"

    if api_file.exists():
        df = pd.read_csv(api_file)

        for customer_id in df["customer_id"].dropna().unique():
            customers.append({
                "source_system": "REST_API",
                "customer_id": clean_value(customer_id),
                "customer_name": None,
                "email": None,
                "city": None,
                "updated_at": pd.Timestamp("1900-01-01").to_pydatetime()
            })

    return customers


# ---------------------------------------------------------
# 4. LOAD CUSTOMER DIMENSION WITH SCD TYPE 2
# ---------------------------------------------------------

def load_customer_dimension(conn, customers):

    inserted = 0
    updated = 0

    # Process customer changes in chronological order
    customers.sort(
        key=lambda x: (
            x["source_system"],
            x["customer_id"],
            x["updated_at"]
        )
    )

    for customer in customers:

        if not customer["customer_id"]:
            continue

        current = conn.execute(
            text("""
                SELECT customer_key, customer_name, email, city,
                       effective_start_date
                FROM dim_customer
                WHERE source_system = :source
                  AND customer_id = :customer_id
                  AND is_current = TRUE
            """),
            {
                "source": customer["source_system"],
                "customer_id": customer["customer_id"]
            }
        ).mappings().first()

        if current is None:

            conn.execute(
                text("""
                    INSERT INTO dim_customer (
                        source_system, customer_id,
                        customer_name, email, city,
                        effective_start_date,
                        effective_end_date, is_current
                    )
                    VALUES (
                        :source_system, :customer_id,
                        :customer_name, :email, :city,
                        :updated_at, NULL, TRUE
                    )
                """),
                customer
            )

            inserted += 1
            continue

        # Ignore records that are not newer than current version
        if customer["updated_at"] <= current["effective_start_date"]:
            continue

        old_values = (
            current["customer_name"],
            current["email"],
            current["city"]
        )

        new_values = (
            customer["customer_name"],
            customer["email"],
            customer["city"]
        )

        # No descriptive change: do not create another version
        if old_values == new_values:
            continue

        # Close the previous customer version
        conn.execute(
            text("""
                UPDATE dim_customer
                SET effective_end_date = :updated_at,
                    is_current = FALSE
                WHERE customer_key = :customer_key
            """),
            {
                "updated_at": customer["updated_at"],
                "customer_key": current["customer_key"]
            }
        )

        # Insert the new customer version
        conn.execute(
            text("""
                INSERT INTO dim_customer (
                    source_system, customer_id,
                    customer_name, email, city,
                    effective_start_date,
                    effective_end_date, is_current
                )
                VALUES (
                    :source_system, :customer_id,
                    :customer_name, :email, :city,
                    :updated_at, NULL, TRUE
                )
            """),
            customer
        )

        inserted += 1
        updated += 1

    return inserted, updated


# ---------------------------------------------------------
# 5. LOAD PRODUCT SOURCE DATA
# ---------------------------------------------------------

def load_product_sources():

    products = []

    # CSV products
    csv_file = BRONZE / "products.csv"

    if csv_file.exists():
        df = pd.read_csv(csv_file)

        for _, row in df.iterrows():
            products.append({
                "source_system": "CSV",
                "product_id": clean_value(row["product_id"]),
                "product_name": clean_value(row["product_name"]),
                "category": clean_value(row["category"]),
                "brand": clean_value(row["brand"]),
                "unit_price": float(row["unit_price"])
            })

    # PostgreSQL products
    pg_file = BRONZE / "postgres_products.csv"

    if pg_file.exists():
        df = pd.read_csv(pg_file)

        for _, row in df.iterrows():
            products.append({
                "source_system": "POSTGRESQL",
                "product_id": clean_value(row["product_id"]),
                "product_name": clean_value(row["product_name"]),
                "category": clean_value(row["category"]),
                "brand": clean_value(row["brand"]),
                "unit_price": float(row["unit_price"])
            })

    # REST API products
    api_file = BRONZE / "api_retail_orders.csv"

    if api_file.exists():
        df = pd.read_csv(api_file)

        df = df.drop_duplicates(subset=["product_id"])

        for _, row in df.iterrows():
            products.append({
                "source_system": "REST_API",
                "product_id": clean_value(row["product_id"]),
                "product_name": clean_value(row["product_name"]),
                "category": None,
                "brand": None,
                "unit_price": float(row["unit_price"])
            })

    return products


# ---------------------------------------------------------
# 6. LOAD PRODUCT DIMENSION
# ---------------------------------------------------------

def load_product_dimension(conn, products):

    inserted = 0
    updated = 0

    # Ensure product identity is unique per source
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_product_source_id
        ON dim_product(source_system, product_id)
    """))

    for product in products:

        result = conn.execute(
            text("""
                INSERT INTO dim_product (
                    source_system, product_id,
                    product_name, category, brand, unit_price
                )
                VALUES (
                    :source_system, :product_id,
                    :product_name, :category, :brand, :unit_price
                )
                ON CONFLICT (source_system, product_id)
                DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    category = EXCLUDED.category,
                    brand = EXCLUDED.brand,
                    unit_price = EXCLUDED.unit_price
                RETURNING (xmax = 0) AS was_inserted
            """),
            product
        ).scalar()

        if result:
            inserted += 1
        else:
            updated += 1

    return inserted, updated


# ---------------------------------------------------------
# 7. MAIN EXECUTION
# ---------------------------------------------------------

def main():

    print("Starting dimension loading...")

    customers = load_customer_sources()
    products = load_product_sources()

    with engine.begin() as conn:

        customer_inserted, customer_updated = (
            load_customer_dimension(conn, customers)
        )

        product_inserted, product_updated = (
            load_product_dimension(conn, products)
        )

        customer_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_customer")
        ).scalar()

        product_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_product")
        ).scalar()

        current_customers = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM dim_customer
                WHERE is_current = TRUE
            """)
        ).scalar()

    print("\nDimension loading completed!")
    print("--------------------------------")
    print(f"Customer source records: {len(customers)}")
    print(f"Customer versions inserted: {customer_inserted}")
    print(f"Customer versions updated: {customer_updated}")
    print(f"Total customer history records: {customer_count}")
    print(f"Current customers: {current_customers}")
    print("--------------------------------")
    print(f"Product source records: {len(products)}")
    print(f"Products inserted: {product_inserted}")
    print(f"Products updated: {product_updated}")
    print(f"Total products: {product_count}")


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
