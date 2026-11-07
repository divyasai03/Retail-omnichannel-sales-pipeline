
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Load environment variables
load_dotenv()

# Read database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

try:
    # Safely construct the database connection URL
    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME
    )

    # Create database engine
    engine = create_engine(database_url)

    # Test database connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]

        print("PostgreSQL connection successful!")
        print("Database:", DB_NAME)
        print("PostgreSQL version:", version)

    engine.dispose()

except Exception as error:
    print("Database connection failed!")
    print("Error:", error)
