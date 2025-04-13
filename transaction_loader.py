import json
import pandas as pd
import logging
import uuid
from datetime import datetime
from mongodb_client import get_database
from transaction_model import Transaction

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TransactionLoader:
    """Loads transactions into MongoDB from Plaid or Excel."""

    def __init__(self):
        self.db = get_database()
        self.transactions_collection = self.db['transactions']

        # Create an index on transaction_id for better performance
        self.transactions_collection.create_index("transaction_id", unique=True)

    def save_plaid_transactions(self, plaid_data):
        """
        Saves transactions retrieved from Plaid API to the database.
        - Uses transaction_id as the unique identifier
        - Filters out pending transactions
        - Saves only finalized transactions to the database
        - Preserves original transaction JSON data

        Args:
            plaid_data (dict): Plaid API response containing transactions and accounts

        Returns:
            dict: Result of the operation with details on processed transactions
        """
        if not plaid_data:
            logging.warning("No transactions found in Plaid data.")
            return {"success": False, "message": "No transactions found in Plaid data."}

        try:
            # Assume plaid_data is a list of transaction dicts
            transactions = plaid_data

            # Filter out pending transactions
            non_pending_txns = [txn for txn in transactions if not txn.get('pending', False)]
            pending_count = len(transactions) - len(non_pending_txns)

            logging.info(
                f"Found {len(transactions)} transactions, {pending_count} pending, {len(non_pending_txns)} ready to save"
            )

            if not non_pending_txns:
                return {
                    "success": True,
                    "message": "No non-pending transactions to save",
                    "total": len(transactions),
                    "pending": pending_count,
                    "processed": 0,
                    "inserted": 0,
                    "updated": 0
                }

            # Prepare transactions for database insertion using our Transaction model
            transactions_to_save = [Transaction(txn) for txn in non_pending_txns]

            inserted_count = 0
            updated_count = 0

            # Insert/update transactions in MongoDB using transaction_id as the key
            for transaction in transactions_to_save:
                result = self.transactions_collection.update_one(
                    {"transaction_id": transaction.transaction_id},
                    {"$set": transaction.to_dict()},
                    upsert=True
                )

                if result.upserted_id:
                    inserted_count += 1
                elif result.modified_count:
                    updated_count += 1

            result_summary = {
                "success": True,
                "message": f"Successfully processed {len(transactions_to_save)} non-pending transactions",
                "total": len(transactions),
                "pending": pending_count,
                "processed": len(transactions_to_save),
                "inserted": inserted_count,
                "updated": updated_count
            }

            logging.info(
                f"✅ Processed Plaid transactions: {result_summary['processed']} non-pending, "
                f"{result_summary['inserted']} new, {result_summary['updated']} updated, "
                f"{result_summary['pending']} pending skipped"
            )

            return result_summary

        except Exception as e:
            logging.error(f"❌ Error saving Plaid transactions: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Error saving Plaid transactions: {str(e)}"}
