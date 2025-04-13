# transaction_loader.py
import json

import pandas as pd
import logging
import uuid
from datetime import datetime
from mongodb_client import get_database

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TransactionLoader:
    """Loads transactions into MongoDB from Plaid or Excel."""

    def __init__(self):
        self.db = get_database()
        self.transactions_collection = self.db['transactions']

        # Create an index on transaction_id for better performance
        self.transactions_collection.create_index("transaction_id", unique=True)

    # def save_plaid_transactions(self, plaid_data):
    #     """
    #     Saves transactions retrieved from Plaid API to the database.
    #     - Uses transaction_id as the unique identifier
    #     - Filters out pending transactions
    #     - Saves only finalized transactions to the database
    #
    #     Args:
    #         plaid_data (dict): Plaid API response containing transactions and accounts
    #
    #     Returns:
    #         dict: Result of the operation with details on processed transactions
    #     """
    #     if not plaid_data:
    #         logging.warning("No transactions found in Plaid data.")
    #         return {"success": False, "message": "No transactions found in Plaid data."}
    #
    #     try:
    #         # Extract transactions from the response
    #         transactions = plaid_data
    #
    #         # Filter out pending transactions
    #         non_pending_txns = [txn for txn in transactions if not txn.get('pending', False)]
    #         pending_count = len(transactions) - len(non_pending_txns)
    #
    #         logging.info(f"Found {len(transactions)} transactions, {pending_count} pending, {len(non_pending_txns)} ready to save")
    #
    #         if not non_pending_txns:
    #             return {
    #                 "success": True,
    #                 "message": "No non-pending transactions to save",
    #                 "total": len(transactions),
    #                 "pending": pending_count,
    #                 "processed": 0,
    #                 "inserted": 0,
    #                 "updated": 0
    #             }
    #
    #         # Prepare transactions for database insertion
    #         transactions_to_save = []
    #         for txn in non_pending_txns:
    #             # Create a standardized transaction object
    #             db_txn = {
    #                 "transaction_id": txn.get("transaction_id"),
    #                 "account_id": txn.get("account_id"),
    #                 "name": txn.get("name"),
    #                 "merchant": txn.get("merchant_name", txn.get("name")),
    #                 "amount": txn.get("amount"),
    #                 "date": txn.get("authorized_date").isoformat(),
    #                 "category": None,
    #                 "iso_currency_code": txn.get("iso_currency_code"),
    #             }
    #             transactions_to_save.append(db_txn)
    #
    #         # Insert into MongoDB using the transaction_id as the unique identifier
    #         inserted_count = 0
    #         updated_count = 0
    #
    #         for transaction in transactions_to_save:
    #             # Check if the transaction_id exists and update or insert accordingly
    #             result = self.transactions_collection.update_one(
    #                 {"transaction_id": transaction["transaction_id"]},
    #                 {"$set": transaction},
    #                 upsert=True
    #             )
    #
    #             if result.upserted_id:
    #                 inserted_count += 1
    #             elif result.modified_count:
    #                 updated_count += 1
    #
    #         # Return success status and statistics
    #         result = {
    #             "success": True,
    #             "message": f"Successfully processed {len(transactions_to_save)} non-pending transactions",
    #             "total": len(transactions),
    #             "pending": pending_count,
    #             "processed": len(transactions_to_save),
    #             "inserted": inserted_count,
    #             "updated": updated_count
    #         }
    #
    #         logging.info(
    #             f"✅ Processed Plaid transactions: {result['processed']} non-pending, "
    #             f"{result['inserted']} new, {result['updated']} updated, "
    #             f"{result['pending']} pending skipped"
    #         )
    #
    #         return result
    #
    #     except Exception as e:
    #         logging.error(f"❌ Error saving Plaid transactions: {str(e)}", exc_info=True)
    #         return {"success": False, "message": f"Error saving Plaid transactions: {str(e)}"}
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
            # Extract transactions from the response
            transactions = plaid_data

            # Filter out pending transactions
            non_pending_txns = [txn for txn in transactions if not txn.get('pending', False)]
            pending_count = len(transactions) - len(non_pending_txns)

            logging.info(f"Found {len(transactions)} transactions, {pending_count} pending, {len(non_pending_txns)} ready to save")

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

            # Prepare transactions for database insertion
            transactions_to_save = []
            for txn in non_pending_txns:
                # Create a standardized transaction object
                raw_json = json.loads(json.dumps(txn, default=str))
                db_txn = {
                    "transaction_id": txn.get("transaction_id"),
                    "account_id": txn.get("account_id"),
                    "name": txn.get("name"),
                    "merchant": txn.get("merchant_name", txn.get("name")),
                    "amount": txn.get("amount"),
                    "date": txn.get("authorized_date").isoformat(),
                    "category": None,
                    "iso_currency_code": txn.get("iso_currency_code"),
                    "original_json": raw_json
                }
                transactions_to_save.append(db_txn)

            # Insert into MongoDB using the transaction_id as the unique identifier
            inserted_count = 0
            updated_count = 0

            for transaction in transactions_to_save:
                # Check if the transaction_id exists and update or insert accordingly
                result = self.transactions_collection.update_one(
                    {"transaction_id": transaction["transaction_id"]},
                    {"$set": transaction},
                    upsert=True
                )

                if result.upserted_id:
                    inserted_count += 1
                elif result.modified_count:
                    updated_count += 1

            # Return success status and statistics
            result = {
                "success": True,
                "message": f"Successfully processed {len(transactions_to_save)} non-pending transactions",
                "total": len(transactions),
                "pending": pending_count,
                "processed": len(transactions_to_save),
                "inserted": inserted_count,
                "updated": updated_count
            }

            logging.info(
                f"✅ Processed Plaid transactions: {result['processed']} non-pending, "
                f"{result['inserted']} new, {result['updated']} updated, "
                f"{result['pending']} pending skipped"
            )

            return result

        except Exception as e:
            logging.error(f"❌ Error saving Plaid transactions: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Error saving Plaid transactions: {str(e)}"}





