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


# 🔹 Configure Logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
        link_token_response = service.link_chase_account()
        logging.info(f"✅ Link Token Created: {link_token_response}")
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
        logging.info(f"✅ Access Token Exchanged: {access_token_response}")
        return jsonify(access_token_response)
    except Exception as e:
        logging.error(f"❌ Error exchanging public token: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to exchange public token: {str(e)}"}), 500


@app.route("/validate-token", methods=["GET"])
def validate_token():
    """Validates if a stored token exists and is valid."""
    try:
        logging.info("🔹 Request received: /validate-token")

        # Check database for token
        db = get_database()
        if not db:
            logging.warning("⚠️ Database connection not available")
            return jsonify({"valid": False, "message": "Database connection not available"}), 500

        # Try to find the account document
        account_doc = db.accounts.find_one({"_id": 1})

        if not account_doc or "access_token" not in account_doc:
            logging.info("ℹ️ No access token found in database")
            return jsonify({"valid": False, "message": "No access token found"})

        # We have a token - let's verify it works by trying to get account info
        access_token = account_doc["access_token"]

        # Use Plaid client to verify token by fetching minimal data
        try:
            # You can replace this with a lighter API call if available
            from datetime import datetime, timedelta
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


@app.route("/transactions/get", methods=["POST"])
def get_transactions():
    """Step 4: Fetch transactions using `access_token`."""
    try:
        logging.info("🔹 Request received: /transactions/get")
        # Get date parameters if they exist
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")

        # If no access token provided, try to get from database
        db = get_database()  # Import from mongodb_client
        # if db is not None:
        #     account_doc = db.accounts.find_one({"id": 1})
        #     print(100, account_doc, db)
        #     print(db["accounts"].count_documents({}))
        #     if account_doc and "token_id" in account_doc:
        #         access_token = account_doc["token_id"]
        #         logging.info("✅ Retrieved access token from database")
        #
        #     # If still no access token, return error
        #     if not account_doc:
        #         logging.warning("⚠️ Missing access_token in request and not found in database")
        #         return jsonify({"error": "access_token is required and not found in database"}), 400

        if db is not None:
            # First try to find any document in the accounts collection
            all_docs = list(db.accounts.find())
            print("All documents in accounts collection:", all_docs)

            # Try to find specifically with id=1
            account_doc = db.accounts.find_one({"id": 1})
            print("Document with id=1:", account_doc)

            # Also try without any filter to see what's there
            first_doc = db.accounts.find_one()
            print("First document in collection:", first_doc)

            # Count documents
            count = db.accounts.count_documents({})
            print("Total documents:", count)

            # If we found any document, use it even if it doesn't have id=1
            if not account_doc and first_doc:
                account_doc = first_doc
                print("Using first document instead")

            # Check for either token_id or access_token
            if account_doc:
                if "token_id" in account_doc:
                    access_token = account_doc["token_id"]
                    print("Found token_id:", access_token[:5] + "..." if access_token else "None")
                elif "access_token" in account_doc:
                    access_token = account_doc["access_token"]
                    print("Found access_token:", access_token[:5] + "..." if access_token else "None")


        # Call with provided dates or let service use defaults
        if start_date and end_date:
            transactions = service.get_transactions(access_token, start_date, end_date)
        else:
            transactions = service.get_transactions(access_token)
        print(transactions[0])

        # Check if we got an error back
        if isinstance(transactions, dict) and "error" in transactions:
            logging.warning(f"⚠️ Error from Plaid service: {transactions['error']}")
            return jsonify({"error": transactions["error"]}), 400

        logging.info(f"✅ Transactions Retrieved: {len(transactions)} transactions")
        return jsonify({"transactions": transactions})
    except Exception as e:
        logging.error(f"❌ Error fetching transactions: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500


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
        limit = request.args.get('limit', default=10, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        result = analyzer.top_merchants(limit, start_date, end_date)
        logging.info(f"✅ Top {limit} merchants analysis completed")
        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ Error analyzing top merchants: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to analyze top merchants: {str(e)}"}), 500


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
