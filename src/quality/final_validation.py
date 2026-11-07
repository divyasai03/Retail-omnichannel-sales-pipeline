
# =========================================================
# FINAL END-TO-END DATA WAREHOUSE VALIDATION
# =========================================================

from pathlib import Path
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

engine = create_engine(
    URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "retail_omnichannel_db")
    )
)

def main():

    print("=" * 55)
    print("RETAIL OMNICHANNEL - FINAL PROJECT VALIDATION")
    print("=" * 55)

    unified = pd.read_csv(
        BASE_DIR / "data" / "silver" / "unified_orders.csv"
    )

    checks = []

    with engine.connect() as conn:

        fact_count = conn.execute(
            text("SELECT COUNT(*) FROM fact_sales")
        ).scalar()

        customer_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_customer")
        ).scalar()

        product_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_product")
        ).scalar()

        date_count = conn.execute(
            text("SELECT COUNT(*) FROM dim_date")
        ).scalar()

        current_customers = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM dim_customer
                WHERE is_current = TRUE
            """)
        ).scalar()

        duplicate_facts = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT source_system, order_id, product_id
                    FROM fact_sales
                    GROUP BY source_system, order_id, product_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        missing_dimension_keys = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM fact_sales
                WHERE customer_key IS NULL
                   OR product_key IS NULL
            """)
        ).scalar()

        duplicate_current_customers = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT source_system, customer_id
                    FROM dim_customer
                    WHERE is_current = TRUE
                    GROUP BY source_system, customer_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        ).scalar()

        source_counts = conn.execute(
            text("""
                SELECT source_system, COUNT(*)
                FROM fact_sales
                GROUP BY source_system
                ORDER BY source_system
            """)
        ).all()

        source_results = {
            source: count for source, count in source_counts
        }

        expected_sources = (
            unified.groupby("source_system").size().to_dict()
        )

        checks = [
            ("Unified records match fact records",
             len(unified) == fact_count),

            ("No duplicate fact business keys",
             duplicate_facts == 0),

            ("No missing customer/product keys",
             missing_dimension_keys == 0),

            ("One current version per customer",
             duplicate_current_customers == 0),

            ("Source-wise counts match",
             source_results == expected_sources),

            ("Customer dimension populated",
             customer_count > 0),

            ("Product dimension populated",
             product_count > 0),

            ("Date dimension populated",
             date_count > 0)
        ]

        print(f"\nUnified records: {len(unified)}")
        print(f"Fact sales records: {fact_count}")
        print(f"Customer history records: {customer_count}")
        print(f"Current customers: {current_customers}")
        print(f"Products: {product_count}")
        print(f"Dates: {date_count}")

        print("\nSource reconciliation:")
        for source, count in source_results.items():
            print(f"{source}: {count}")

        print("\nValidation checks:")
        for description, passed in checks:
            print(f"{'PASS' if passed else 'FAIL'} - {description}")

    passed_count = sum(result for _, result in checks)

    print("\n" + "=" * 55)
    print(f"RESULT: {passed_count}/{len(checks)} CHECKS PASSED")

    if passed_count == len(checks):
        print("FINAL PROJECT VALIDATION SUCCESSFUL!")
    else:
        print("VALIDATION FAILED - REVIEW THE CHECKS ABOVE.")
        sys.exit(1)

    print("=" * 55)


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
