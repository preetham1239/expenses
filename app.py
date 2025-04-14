import json

from flask import Flask, jsonify, request
from plaid_service import PlaidService
from flask_cors import CORS
from transaction_loader import TransactionLoader
from transaction_analyzer import TransactionAnalyzer
from mongodb_client import get_database
import logging
import ssl
import os
import traceback
import uuid
import plaid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from transaction_model import Transaction

# 🔹 Configure Logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)


# Global variables for database connection and access token
db = None
access_token = None

app = Flask(__name__)
service = PlaidService()
loader = TransactionLoader()
analyzer = TransactionAnalyzer()

# 🔹 Set Upload Folder for Excel Files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# 🔹 Enhanced CORS Configuration for Plaid
CORS(app, resources={r"/*": {
    "origins": [
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "supports_credentials": True,
    "expose_headers": ["Content-Type", "Authorization"]
}})


# Initialize database connection and load access token at startup
def initialize_app():
    global db, access_token
    logging.info("🔹 Initializing application...")

    # Connect to database
    db = get_database()
    if db is None:
        logging.warning("⚠️ Failed to connect to database during initialization")
    else:
        logging.info("✅ Successfully connected to database")

        # Try to load access token
        try:
            account_doc = db.accounts.find_one({"id": "1"})
            if account_doc:
                if "token_id" in account_doc:
                    access_token = account_doc["token_id"]
                    logging.info("✅ Successfully loaded access token from database")
                elif "access_token" in account_doc:
                    access_token = account_doc["access_token"]
                    logging.info("✅ Successfully loaded access token from database")
                else:
                    logging.info("ℹ️ No access token found in the database")
            else:
                logging.info("ℹ️ No account document found in the database")
        except Exception as e:
            logging.error(f"❌ Error loading access token: {str(e)}")


def get_last_month_date_range():
    today = datetime.today()
    first_day_this_month = datetime(today.year, today.month, 1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = datetime(last_day_last_month.year, last_day_last_month.month, 1)
    return first_day_last_month.strftime('%Y-%m-%d'), last_day_last_month.strftime('%Y-%m-%d')


# Helper function to update access token in both global variable and database
def update_access_token(token):
    global access_token, db
    access_token = token

    # Also update in database if available
    if db is not None:
        try:
            result = db.accounts.update_one(
                {"id": "1"},
                {"$set": {
                    "token_id": token,
                    "last_updated": datetime.now().isoformat()
                }},
                upsert=True
            )

            if result.upserted_id:
                logging.info(f"✅ New account record created with access token (ID: {result.upserted_id})")
            else:
                logging.info("✅ Existing account record updated with new access token")

            logging.info("✅ Access token updated in both global variable and database")
        except Exception as e:
            logging.error(f"❌ Error updating access token in database: {str(e)}")
    else:
        logging.info("✅ Global access token updated (database not available)")



# Helper function to check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Add custom headers to every response for Plaid
@app.after_request
def add_plaid_headers(response):
    # Set headers needed for Plaid Link to work
    response.headers['Access-Control-Allow-Origin'] = 'https://localhost:3000'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

    # Allow Plaid's iframe
    response.headers['Permissions-Policy'] = 'fullscreen=*, payment=*'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'

    # Set Content-Security-Policy to allow Plaid frames
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://cdn.plaid.com"

    return response


@app.route("/link/token/create", methods=["POST"])
def create_link_token():
    """Step 1: Generate a Link Token for user authentication."""
    try:
        logging.info("🔹 Request received: /link/token/create")

        # Check if we already have a valid token in our global variable
        force_new_token = request.json.get("force_new_token", False)

        if access_token is not None and not force_new_token:
            logging.info("✅ Valid access token exists, skipping link token creation")
            return jsonify({"existing_token": True, "message": "Using existing token"})

        # Proceed with link token creation if needed
        link_token_response = service.link_chase_account()
        logging.info("✅ Link Token Created")
        return jsonify(link_token_response.to_dict())
    except Exception as e:
        logging.error(f"❌ Error generating link token: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to generate link token: {str(e)}"}), 500


@app.route("/item/public_token/exchange", methods=["POST"])
def exchange_public_token():
    """Step 3: Exchange a `public_token` for a permanent `access_token`."""
    try:
        logging.info("🔹 Request received: /item/public_token/exchange")
        public_token = request.json.get("public_token")
        if not public_token:
            logging.warning("⚠️ Missing public_token in request")
            return jsonify({"error": "public_token is required"}), 400

        access_token_response = service.exchange_public_token(public_token)

        # Update the global access token and database
        if "access_token" in access_token_response:
            update_access_token(access_token_response["access_token"])
            logging.info("✅ New access token saved")
        else:
            logging.warning("⚠️ No access_token in Plaid response")

        logging.info("✅ Access Token Exchanged")
        return jsonify(access_token_response)
    except Exception as e:
        logging.error(f"❌ Error exchanging public token: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to exchange public token: {str(e)}"}), 500


@app.route("/validate-token", methods=["GET"])
def validate_token():
    """Validates if a stored token exists and is valid."""
    try:
        logging.info("🔹 Request received: /validate-token")

        # Check the global access token
        if access_token is None:
            logging.info("ℹ️ No access token available")
            return jsonify({"valid": False, "message": "No access token found"})

        # Use Plaid client to verify token by fetching minimal data
        try:
            # Get the last 1 day of transactions to verify token
            start_date = (datetime.now() - timedelta(days=1)).date()
            end_date = datetime.now().date()

            # Use the client directly to avoid circular imports
            from plaid_client import PlaidClient
            client = PlaidClient()

            # Try to get a small amount of data to verify the token works
            response = client.client.transactions_get(
                plaid.model.transactions_get_request.TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=plaid.model.transactions_get_request_options.TransactionsGetRequestOptions(
                        count=1
                    )
                )
            )

            # If we get here, the token is valid
            logging.info("✅ Access token is valid")
            return jsonify({"valid": True, "message": "Token is valid"})

        except Exception as e:
            logging.error(f"❌ Error validating token: {str(e)}")
            # Token might be expired or invalid
            return jsonify({"valid": False, "message": "Token validation failed"})

    except Exception as e:
        logging.error(f"❌ Error in token validation: {str(e)}")
        return jsonify({"valid": False, "message": f"Error validating token: {str(e)}"}), 500


@app.route("/transactions/get-from-db", methods=["POST"])
def get_transactions_from_db():
    """Get transactions directly from MongoDB database with pagination support."""
    try:
        logging.info("🔹 Request received: /transactions/get-from-db")

        # Check if we have a database connection
        if db is None:
            logging.error("❌ Database connection not available")
            return jsonify({"error": "Database connection failed"}), 500

        # Get filter parameters
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")
        limit = int(request.json.get("limit", 1000))  # Default to 1000

        # Build query filters
        query = {}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["date"] = date_filter

        # Execute query
        transactions = list(db.transactions.find(query).sort("date", -1).limit(limit))

        # Convert ObjectId to string for JSON serialization
        for txn in transactions:
            if "_id" in txn:
                txn["_id"] = str(txn["_id"])

        # Get total count for pagination
        total_count = db.transactions.count_documents(query)
        logging.info(f"✅ Retrieved {len(transactions)} transactions out of {total_count} matching documents")

        return jsonify({
            "transactions": transactions,
            "total_count": total_count,
            "returned_count": len(transactions)
        })
    except Exception as e:
        logging.error(f"❌ Error fetching transactions from DB: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500


@app.route("/transactions/get", methods=["POST"])
def get_transactions():
    """Fetch transactions using `access_token` with pagination support."""
    try:
        logging.info("🔹 Request received: /transactions/get")

        # Try to get token from request first, then fall back to global
        token = access_token

        # Check if we have a valid token
        if token is None:
            logging.warning("⚠️ No access token available")
            return jsonify({"error": "No access token available"}), 400

        # Get date parameters
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")
        limit = min(request.json.get("limit", 1000), 1000)

        if not start_date or not end_date:
            start_date, end_date = get_last_month_date_range()

        # Call Plaid service
        if start_date and end_date:
            plaid_transactions = service.get_transactions(token, start_date, end_date, limit)
        else:
            plaid_transactions = service.get_transactions(token, limit=limit)

        # Check if we got an error back
        if isinstance(plaid_transactions, dict) and "error" in plaid_transactions:
            logging.warning(f"⚠️ Error from Plaid service: {plaid_transactions['error']}")
            return jsonify({"error": plaid_transactions["error"]}), 400

        logging.info(f"✅ Transactions Retrieved: {len(plaid_transactions)} transactions")

        save_result = loader.save_plaid_transactions(plaid_transactions)
        logging.info(f"✅ Saved transactions to database: {save_result}")
        return jsonify({"transactions": plaid_transactions})
    except Exception as e:
        logging.error(f"❌ Error fetching transactions: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500


@app.route('/transactions/update', methods=['PUT'])
def update_transaction():
    """Update a transaction in the database."""
    try:
        logging.info("🔹 Request received: /transactions/update")

        # Check if we have a database connection
        if db is None:
            logging.error("❌ Database connection not available")
            return jsonify({"error": "Database connection failed"}), 500

        # Get transaction data from request
        transaction_data = request.json

        if not transaction_data or 'transaction_id' not in transaction_data:
            logging.warning("⚠️ Missing transaction_id in request")
            return jsonify({"error": "transaction_id is required"}), 400

        transaction_id = transaction_data.get('transaction_id')

        # Prepare update data
        update_fields = {
            "name": transaction_data.get("name"),
            "amount": transaction_data.get("amount"),
            "date": transaction_data.get("date"),
            "category": transaction_data.get("category")
        }

        # Remove None values
        update_fields = {k: v for k, v in update_fields.items() if v is not None}

        if not update_fields:
            logging.warning("⚠️ No fields to update")
            return jsonify({"error": "No fields to update"}), 400

        # Perform update
        result = db.transactions.update_one(
            {"transaction_id": transaction_id},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            logging.warning(f"⚠️ Transaction not found: {transaction_id}")
            return jsonify({"error": "Transaction not found"}), 404

        logging.info(f"✅ Transaction updated: {transaction_id}")
        return jsonify({
            "success": True,
            "message": "Transaction updated successfully",
            "transaction_id": transaction_id
        })

    except Exception as e:
        logging.error(f"❌ Error updating transaction: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to update transaction: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle transaction data file uploads (Excel or CSV)."""
    try:
        logging.info("🔹 Request received: /upload")

        # Check if a file was included in the request
        if 'file' not in request.files:
            logging.warning("⚠️ No file part in the request")
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        # Check if the user submitted an empty form
        if file.filename == '':
            logging.warning("⚠️ No file selected")
            return jsonify({"error": "No file selected"}), 400

        # Check if the file type is allowed
        if file and allowed_file(file.filename):
            # Create a unique filename to prevent overwriting
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

            # Save the file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Process the file and load transactions
            result = loader.load_from_excel(filepath)

            logging.info(f"✅ File uploaded and processed: {original_filename}")
            return jsonify({
                "success": True,
                "message": "File uploaded and processed successfully",
                "original_filename": original_filename,
                "result": result
            })
        else:
            logging.warning(f"⚠️ File type not allowed: {file.filename}")
            return jsonify({
                "error": f"File type not allowed. Please upload a file with one of these extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

    except Exception as e:
        logging.error(f"❌ Error uploading file: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500


@app.route('/analysis/spending-by-category', methods=['GET'])
def spending_by_category():
    """Analyze spending by category."""
    try:
        logging.info("🔹 Request received: /analysis/spending-by-category")

        # Check if we have a database connection
        if db is None:
            logging.error("❌ Database connection not available")
            return jsonify({"error": "Database connection failed"}), 500

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        result = analyzer.spending_by_category(start_date, end_date)
        logging.info("✅ Spending by category analysis completed")
        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ Error analyzing spending by category: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to analyze spending: {str(e)}"}), 500


@app.route('/analysis/monthly-trend', methods=['GET'])
def monthly_trend():
    """Analyze monthly spending trends."""
    try:
        logging.info("🔹 Request received: /analysis/monthly-trend")

        # Check if we have a database connection
        if db is None:
            logging.error("❌ Database connection not available")
            return jsonify({"error": "Database connection failed"}), 500

        year = request.args.get('year')

        result = analyzer.monthly_spending_trend(year)
        logging.info("✅ Monthly spending trend analysis completed")
        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ Error analyzing monthly trend: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to analyze monthly trend: {str(e)}"}), 500


@app.route('/analysis/top-merchants', methods=['GET'])
def top_merchants():
    """Get top merchants by spending amount."""
    try:
        logging.info("🔹 Request received: /analysis/top-merchants")

        # Check if we have a database connection
        if db is None:
            logging.error("❌ Database connection not available")
            return jsonify({"error": "Database connection failed"}), 500

        limit = request.args.get('limit', default=10, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        result = analyzer.top_merchants(limit, start_date, end_date)
        logging.info(f"✅ Top {limit} merchants analysis completed")
        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ Error analyzing top merchants: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to analyze top merchants: {str(e)}"}), 500


# Initialize the app before running
initialize_app()

if __name__ == "__main__":
    # 🔹 Load SSL Certificates for HTTPS
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("frontend/localhost+1.pem", "frontend/localhost+1-key.pem")
        logging.info("✅ SSL certificates loaded successfully")
    except Exception as e:
        logging.error(f"❌ SSL certificate error: {str(e)}")
        logging.error(traceback.format_exc())

    logging.info("🚀 Starting Flask Server on port 8000")
    app.run(host="localhost", port=8000, debug=True, ssl_context=context)
