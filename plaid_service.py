import logging
from plaid_client import PlaidClient
from mongodb_client import get_database

# Configure logging instead of print statements
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PlaidService:
    """Handles transaction retrieval and authentication with Plaid."""

    def __init__(self):
        self.client = PlaidClient()
        self.db = get_database()

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

            # Store the access token in the database
            if self.db:
                self.db.accounts.update_one(
                    {"_id": 1},
                    {"$set": {"access_token": access_token}},
                    upsert=True
                )
                logging.info("✅ Access Token stored in database.")

            logging.info("✅ Access Token retrieved successfully.")
            return {"access_token": access_token}
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}

    def get_transactions(self, access_token=None, start_date=None, end_date=None):
        """Retrieves transactions from Plaid API or uses stored token."""
        # Default dates if not provided
        from datetime import datetime, timedelta

        # If no start_date provided, use 30 days ago
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # If no end_date provided, use today
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # First, try to get access token from parameter
        if not access_token:
            # If not provided, try to get from database
            if self.db is not None:
                account_doc = self.db.accounts.find_one({"id": 1})
                if account_doc and "token_id" in account_doc:
                    access_token = account_doc["token_id"]
                    logging.info("✅ Retrieved access token from database.")

        if not access_token:
            logging.warning("❌ Access token is missing and not found in database.")
            return {"error": "access_token is required and not found in database"}

        try:
            transactions = self.client.get_transactions(access_token, start_date, end_date)
            logging.info(f"🔄 Retrieved {len(transactions)} transactions.")
            return transactions
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

            # Store the access token in the database
            if hasattr(response, 'to_dict'):
                response_dict = response.to_dict()
            else:
                response_dict = response

            if self.db and "access_token" in response_dict:
                self.db.accounts.update_one(
                    {"_id": 1},
                    {"$set": {"access_token": response_dict["access_token"]}},
                    upsert=True
                )
                logging.info("✅ Access Token stored in database.")

            logging.info("✅ Public token successfully exchanged for access token.")
            return response_dict
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}

