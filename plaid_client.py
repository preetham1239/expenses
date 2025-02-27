import logging
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from config import Config
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

# Configure logging for production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PlaidClient:
    """Handles API requests using the Plaid SDK for Production."""

    def __init__(self):
        # Set Plaid API environment
        self.configuration = Configuration(
            host="https://production.plaid.com" if Config.PLAID_ENV == "production" else "https://sandbox.plaid.com"
        )
        self.configuration.api_key["clientId"] = Config.PLAID_CLIENT_ID
        self.configuration.api_key["secret"] = Config.PLAID_SECRET
        self.api_client = ApiClient(self.configuration)
        self.client = plaid_api.PlaidApi(self.api_client)

    def get_transactions(self, access_token, start_date="2024-01-01", end_date="2024-02-01"):
        """Fetches transactions from Plaid API securely."""
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=TransactionsGetRequestOptions(count=100)
            )
            response = self.client.transactions_get(request)
            transactions = response.to_dict()["transactions"]
            logging.info(f"🔄 Retrieved {len(transactions)} transactions.")
            return transactions
        except Exception as e:
            logging.error(f"❌ Failed to fetch transactions: {str(e)}")
            return {"error": f"Failed to fetch transactions: {str(e)}"}

    def create_link_token(self):
        """Generates a Plaid Link Token for user authentication."""
        try:
            request = LinkTokenCreateRequest(
                user={"client_user_id": "unique_user_id"},
                client_name="My App",
                products=[Products("transactions")],
                country_codes=[CountryCode("US")],
                language="en",
                # institution
                # redirect_uri=Config.PLAID_REDIRECT_URI  # Required for OAuth banks
            )
            response = self.client.link_token_create(request)
            logging.info("🔗 Link Token successfully generated.")
            return response.to_dict()
        except Exception as e:
            logging.error(f"❌ Failed to create link token: {str(e)}")
            return {"error": f"Failed to create link token: {str(e)}"}

    def exchange_public_token(self, public_token):
        """Exchanges a `public_token` for a permanent `access_token`."""
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            logging.info("✅ Public token successfully exchanged for access token.")
            return response.to_dict()
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}
