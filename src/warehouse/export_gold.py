
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
GOLD_DIR = BASE_DIR / "data" / "gold"

load_dotenv(BASE_DIR / ".env")

database_url = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(database_url)
GOLD_DIR.mkdir(parents=True, exist_ok=True)

queries = {
    "sales_summary_by_source.csv": """
        SELECT
            source_system,
            COUNT(*) AS sales_records,
            SUM(quantity) AS total_quantity,
            ROUND(SUM(total_amount)::numeric, 2) AS recorded_amount
        FROM fact_sales
        GROUP BY source_system
        ORDER BY source_system;
    """,

    "sales_summary_by_product.csv": """
        SELECT
            dp.source_system,
            dp.product_id,
            dp.product_name,
            SUM(fs.quantity) AS total_quantity,
            ROUND(SUM(fs.total_amount)::numeric, 2) AS recorded_amount
        FROM fact_sales fs
        JOIN dim_product dp
            ON fs.product_key = dp.product_key
        GROUP BY
            dp.source_system,
            dp.product_id,
            dp.product_name
        ORDER BY recorded_amount DESC;
    """,

    "sales_summary_by_city.csv": """
        SELECT
            dc.source_system,
            COALESCE(dc.city, 'Not Available') AS city,
            COUNT(*) AS sales_records,
            SUM(fs.quantity) AS total_quantity,
            ROUND(SUM(fs.total_amount)::numeric, 2) AS recorded_amount
        FROM fact_sales fs
        JOIN dim_customer dc
            ON fs.customer_key = dc.customer_key
           AND dc.is_current = TRUE
        GROUP BY
            dc.source_system,
            COALESCE(dc.city, 'Not Available')
        ORDER BY dc.source_system, city;
    """
}

try:
    with engine.connect() as connection:
        for filename, query in queries.items():
            df = pd.read_sql(query, connection)
            output_path = GOLD_DIR / filename
            df.to_csv(output_path, index=False)

            print(f"Created: {filename}")
            print(f"Records: {len(df)}")

    print("\nGold layer exports completed successfully!")

finally:
    engine.dispose()
