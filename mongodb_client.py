from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=".env")

# Get MongoDB connection details
MONGO_USER = os.getenv("DB_USER")
MONGO_PASSWORD = os.getenv("DB_PASSWORD")
MONGO_HOST = os.getenv("DB_HOST", "localhost")
MONGO_PORT = os.getenv("DB_PORT", "27017")
MONGO_DB = os.getenv("DB_NAME", "expenses")
MONGO_AUTH_SOURCE = os.getenv("DB_AUTH_SOURCE", "admin")  # Added auth source parameter

# URL encode username and password for special characters
if MONGO_USER:
    MONGO_USER_ENCODED = urllib.parse.quote_plus(MONGO_USER)
else:
    MONGO_USER_ENCODED = MONGO_USER

if MONGO_PASSWORD:
    MONGO_PASSWORD_ENCODED = urllib.parse.quote_plus(MONGO_PASSWORD)
else:
    MONGO_PASSWORD_ENCODED = MONGO_PASSWORD

# Create MongoDB connection string with encoded credentials
if MONGO_USER_ENCODED and MONGO_PASSWORD_ENCODED:
    MONGO_URI = f"mongodb://{MONGO_USER_ENCODED}:{MONGO_PASSWORD_ENCODED}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource={MONGO_AUTH_SOURCE}"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"

# Masked password for logging
if MONGO_PASSWORD:
    password_masked = "*" * len(MONGO_PASSWORD)
else:
    password_masked = "None"

logger.info("="*50)
logger.info("MONGODB CONNECTION DETAILS:")
logger.info(f"Username: {MONGO_USER}")
logger.info(f"Password: {password_masked}")
logger.info(f"Host: {MONGO_HOST}")
logger.info(f"Port: {MONGO_PORT}")
logger.info(f"Database: {MONGO_DB}")
logger.info(f"Auth Source: {MONGO_AUTH_SOURCE}")
logger.info(f"Connection string format: mongodb://username:******@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource={MONGO_AUTH_SOURCE}")
logger.info("="*50)

# Global client and db variables
client = None
db = None


def get_database():
    """
    Returns the MongoDB database instance.
    If not connected, attempts to connect first.
    If connection fails, returns an in-memory fallback.
    """
    global client, db

    if db is not None:
        return db

    try:
        # Create a MongoDB client if not already created
        if client is None:
            # Print URI for debugging (hide password in logs)
            debug_uri = MONGO_URI.replace(MONGO_PASSWORD_ENCODED or "", "******") if MONGO_PASSWORD_ENCODED else MONGO_URI
            logger.info(f"Attempting to connect with URI: {debug_uri}")

            client = MongoClient(MONGO_URI,
                                 serverSelectionTimeoutMS=5000,
                                 connectTimeoutMS=5000,
                                 socketTimeoutMS=10000)

            # Validate connection
            client.admin.command('ping')  # A lighter way to check connection
            logger.info("✅ Successfully connected to MongoDB")

        # Get the database
        db = client[MONGO_DB]
        return db

    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.warning("Using in-memory fallback for database operations")
        return None  # Changed to return None instead of db which would be None here


def check_connection():
    """Tests the database connection and prints status."""
    global client

    try:
        if client is None:
            get_database()  # This will attempt to create a connection

        if client is not None:
            # Try to execute a simple command
            info = client.server_info()
            logger.info("✅ MongoDB connection successful!")
            logger.info(f"MongoDB version: {info.get('version')}")
            return True

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")

    return False


# # Uncomment to test when running this file directly
# if __name__ == "__main__":
#     check_connection()
