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

    # Make sure we have a proper HTTPS URL for the redirect URI
    # This is required for OAuth flows with Plaid
    PLAID_REDIRECT_URI = os.getenv("PLAID_REDIRECT_URI", "https://localhost:3000/oauth-callback")

    # Database credentials
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")

    @classmethod
    def validate(cls):
        """Validates critical configuration settings."""
        missing = []
        if not cls.PLAID_CLIENT_ID:
            missing.append("PLAID_CLIENT_ID")
        if not cls.PLAID_SECRET:
            missing.append("PLAID_SECRET")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Validate Plaid environment
        valid_envs = ["sandbox", "development", "production"]
        if cls.PLAID_ENV.lower() not in valid_envs:
            raise ValueError(f"PLAID_ENV must be one of: {', '.join(valid_envs)}")

        # Validate redirect URI for OAuth flows
        if cls.PLAID_REDIRECT_URI and not cls.PLAID_REDIRECT_URI.startswith("https://"):
            print(f"WARNING: PLAID_REDIRECT_URI should use HTTPS. Current value: {cls.PLAID_REDIRECT_URI}")

        return True