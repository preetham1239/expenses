import os
from dotenv import load_dotenv

class Config:
    """Loads environment variables securely."""
    load_dotenv(dotenv_path=".env")

    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET = os.getenv("PLAID_SECRET")
    PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
    PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
    PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")
    PLAID_REDIRECT_URI = os.getenv("PLAID_REDIRECT_URI")

    # Database credentials
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
