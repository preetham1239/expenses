from flask import Flask, jsonify, request
from plaid_service import PlaidService
from flask_cors import CORS
from transaction_loader import TransactionLoader
import logging
import ssl
import os
import traceback

# 🔹 Configure Logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = Flask(__name__)
service = PlaidService()
loader = TransactionLoader()

# 🔹 Set Upload Folder for Excel Files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        return jsonify(link_token_response)
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


@app.route("/transactions/get", methods=["POST"])
def get_transactions():
    """Step 4: Fetch transactions using `access_token`."""
    try:
        logging.info("🔹 Request received: /transactions/get")
        access_token = request.json.get("access_token")
        if not access_token:
            logging.warning("⚠️ Missing access_token in request")
            return jsonify({"error": "access_token is required"}), 400

        transactions = service.get_transactions(access_token)
        logging.info(f"✅ Transactions Retrieved: {len(transactions)} transactions")
        return jsonify({"transactions": transactions})
    except Exception as e:
        logging.error(f"❌ Error fetching transactions: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500


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
