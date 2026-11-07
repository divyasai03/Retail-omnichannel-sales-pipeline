
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Find project directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Load database credentials from .env
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Bronze output directory
BRONZE_DIR = BASE_DIR / "data" / "bronze"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# PostgreSQL tables and their output CSV files
TABLES = {
    "source_customers": "postgres_customers.csv",
    "source_products": "postgres_products.csv",
    "source_orders": "postgres_orders.csv"
}

def main():

    print("Starting PostgreSQL ingestion...")

    # Safely construct database URL
    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME
    )

    engine = create_engine(database_url)

    try:
        for table_name, output_file in TABLES.items():

            # Extract data from PostgreSQL
            query = f"SELECT * FROM {table_name}"

            df = pd.read_sql(query, engine)

            # Save extracted data into Bronze
            output_path = BRONZE_DIR / output_file

            df.to_csv(output_path, index=False)

            print(
                f"{table_name}: {len(df)} records ingested successfully"
            )

            print(f"Bronze file: {output_path}")

        print("\nPostgreSQL ingestion completed!")

    except Exception as error:
        print("\nPostgreSQL ingestion failed!")
        print("Error:", error)
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
