import logging
from plaid_client import PlaidClient

# Configure logging instead of print statements
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PlaidService:
    """Handles transaction retrieval and authentication with Plaid."""

    def __init__(self):
        self.client = PlaidClient()

    def link_chase_account(self):
        """Generates a Link Token for Plaid authentication in production."""
        try:
            link_token_response = self.client.create_link_token()
            logging.info("🔗 Link Token generated successfully.")
            return link_token_response
        except Exception as e:
            logging.error(f"❌ Failed to generate link token: {str(e)}")
            return {"error": f"Failed to generate link token: {str(e)}"}

    def authenticate_and_get_access_token(self, public_token):
        """Authenticates user and retrieves access token."""
        if not public_token:
            logging.warning("❌ Public token is missing.")
            return {"error": "public_token is required"}

        try:
            response = self.client.exchange_public_token(public_token)
            access_token = response["access_token"]
            logging.info("✅ Access Token retrieved successfully.")
            return {"access_token": access_token}
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}

    def get_transactions(self, access_token, start_date="2024-01-01", end_date="2024-02-01"):
        """Retrieves transactions from Plaid API."""
        if not access_token:
            logging.warning("❌ Access token is missing.")
            return {"error": "access_token is required"}

        try:
            transactions_response = self.client.get_transactions(access_token, start_date, end_date)
            transactions = transactions_response.get("transactions", [])
            logging.info(f"🔄 Retrieved {len(transactions)} transactions.")
            return {"transactions": transactions}
        except Exception as e:
            logging.error(f"❌ Failed to fetch transactions: {str(e)}")
            return {"error": f"Failed to fetch transactions: {str(e)}"}

    def exchange_public_token(self, public_token):
        """Exchanges a `public_token` for a permanent `access_token`."""
        if not public_token:
            logging.warning("❌ Public token is missing.")
            return {"error": "public_token is required"}

        try:
            response = self.client.exchange_public_token(public_token)
            logging.info("✅ Public token successfully exchanged for access token.")
            return response.to_dict()
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}
