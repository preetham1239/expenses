from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a database engine
engine = create_engine(DATABASE_URL)


def get_engine():
    """Returns a database connection engine."""
    return engine


def check_connection():
    """Tests the database connection and prints status."""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")  # Simple query to test connection
            if result.fetchone()[0] == 1:
                print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

