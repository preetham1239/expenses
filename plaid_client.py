import logging
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from config import Config
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from datetime import datetime, date, timedelta

# Configure logging for production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PlaidClient:
    """Handles API requests using the Plaid SDK for Production."""

    def __init__(self):
        # Set Plaid API environment
        plaid_env = Config.PLAID_ENV.lower()
        host_map = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com"
        }

        host = host_map.get(plaid_env, "https://sandbox.plaid.com")
        logging.info(f"Initializing Plaid client with environment: {plaid_env}, host: {host}")

        self.configuration = Configuration(host=host)
        self.configuration.api_key["clientId"] = Config.PLAID_CLIENT_ID
        self.configuration.api_key["secret"] = Config.PLAID_SECRET
        self.api_client = ApiClient(self.configuration)
        self.client = plaid_api.PlaidApi(self.api_client)

    def _parse_date(self, date_str):
        """Converts a date string to a date object required by Plaid API."""
        if isinstance(date_str, (date, datetime)):
            # If it's already a date or datetime object, convert to date
            return date_str.date() if isinstance(date_str, datetime) else date_str

        try:
            # Try to parse the string into a date object
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            return parsed_date
        except Exception as e:
            logging.error(f"❌ Error parsing date {date_str}: {e}")
            # Return today's date as fallback
            return datetime.now().date()

    def get_transactions(self, access_token, limit, start_date=None, end_date=None):
        """Fetches transactions from Plaid API securely with pagination.

        Args:
            access_token (str): Plaid access token
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            limit (int): Maximum number of transactions to retrieve (default 500)

        Returns:
            list: List of transaction objects
        """
        try:
            # Ensure we're using the provided dates
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                logging.info(f"No start_date provided, using default: {start_date}")
            else:
                logging.info(f"Using provided start_date: {start_date}")

            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                logging.info(f"No end_date provided, using default: {end_date}")
            else:
                logging.info(f"Using provided end_date: {end_date}")

            # Convert date strings to actual date objects
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)

            logging.info(f"Making Plaid API request with date range: {start_date_obj} to {end_date_obj}, limit: {limit}")

            # Initialize variables for pagination
            all_transactions = []
            has_more = True
            cursor = None

            # Use pagination to get all transactions
            while has_more:
                # Prepare options with cursor if we have one
                options = TransactionsGetRequestOptions(
                    count=limit  # Maximum per request
                )

                if cursor:
                    options.cursor = cursor

                # Make the request
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    options=options
                )

                response = self.client.transactions_get(request)
                response_dict = response.to_dict()

                # Get transactions from this batch
                batch_transactions = response_dict["transactions"]
                all_transactions.extend(batch_transactions)

                # Check if there are more transactions to fetch
                has_more = response_dict.get("has_more", False)

                # Get cursor for next page if there is one
                if has_more:
                    cursor = response_dict.get("next_cursor")
                    logging.info(f"Retrieved {len(batch_transactions)} transactions, fetching more with cursor")

                # Check if we've reached the requested limit
                if limit and len(all_transactions) >= limit:
                    all_transactions = all_transactions[:limit]
                    has_more = False
                    logging.info(f"Reached limit of {limit} transactions, stopping pagination")

                # Safety check to prevent infinite loops
                if len(all_transactions) > 10000:
                    logging.warning("Retrieved over 10,000 transactions, stopping to prevent excessive API calls")
                    has_more = False

            logging.info(f"🔄 Retrieved {len(all_transactions)} transactions from {start_date_obj} to {end_date_obj}")
            return all_transactions
        except Exception as e:
            logging.error(f"❌ Failed to fetch transactions: {str(e)}")
            return {"error": f"Failed to fetch transactions: {str(e)}"}

    def create_link_token(self):
        """Generates a Plaid Link Token for user authentication."""
        try:
            # Create a unique user ID for this session
            import uuid
            unique_user_id = str(uuid.uuid4())
            logging.info(f"Creating link token for user ID: {unique_user_id}")

            # Build the request
            user = LinkTokenCreateRequestUser(client_user_id=unique_user_id)

            # Create the request object with proper models
            request = LinkTokenCreateRequest(
                user=user,
                client_name="Expense Tracker",
                products=[Products("transactions")],
                country_codes=[CountryCode("US")],
                language="en",
                redirect_uri=Config.PLAID_REDIRECT_URI if hasattr(Config, 'PLAID_REDIRECT_URI') else None
            )

            # Execute the API call
            response = self.client.link_token_create(request)
            link_token_data = response

            # Log a portion of the token for debugging (not the full token for security)
            token_preview = link_token_data.get('link_token', '')[:10] + '...' if link_token_data.get('link_token') else 'None'
            logging.info(f"🔗 Link Token successfully generated: {token_preview}")

            return link_token_data
        except Exception as e:
            logging.error(f"❌ Failed to create link token: {str(e)}", exc_info=True)
            return {"error": f"Failed to create link token: {str(e)}"}

    def exchange_public_token(self, public_token):
        """Exchanges a `public_token` for a permanent `access_token`."""
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)

            response_dict = response

            # Log a portion of the access token for debugging (not the full token for security)
            token_preview = response_dict.get('access_token', '')[:10] + '...' if response_dict.get('access_token') else 'None'
            logging.info(f"✅ Public token successfully exchanged for access token: {token_preview}")

            return response_dict
        except Exception as e:
            logging.error(f"❌ Failed to exchange public token: {str(e)}")
            return {"error": f"Failed to exchange public token: {str(e)}"}

