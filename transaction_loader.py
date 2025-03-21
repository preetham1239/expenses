# transaction_loader.py
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

    def load_from_plaid(self, transactions):
        """
        Loads transactions from Plaid API response into MongoDB.
        
        Args:
            transactions (list): List of transaction dictionaries from Plaid API
            
        Returns:
            dict: Result of the operation
        """
        if not transactions:
            logging.warning("No transactions to load.")
            return {"success": False, "message": "No transactions to load."}

        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(transactions)

            # Ensure required columns exist
            required_columns = ["transaction_id", "account_id", "name", "amount", "date", "category"]
            for col in required_columns:
                if col not in df.columns:
                    if col == "category":
                        # Category might be in a different format in Plaid data
                        if "category" in df.columns:
                            # If category is a list, convert to string
                            if isinstance(df["category"].iloc[0], list):
                                df["category"] = df["category"].apply(lambda x: x[0] if x else "Uncategorized")
                        else:
                            df["category"] = "Uncategorized"
                    elif col == "transaction_id":
                        # Ensure transaction ID is unique
                        if "id" in df.columns:
                            df["transaction_id"] = df["id"]
                        else:
                            # Generate UUID if missing
                            df["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
                    else:
                        logging.error(f"Required column {col} missing from Plaid data.")
                        return {"success": False, "message": f"Required column {col} missing from Plaid data."}

            # Select and rename columns
            df = df[required_columns]

            # Clean data
            df = self._clean_transaction_data(df)

            # Convert to list of dictionaries for MongoDB
            transactions_to_insert = df.to_dict('records')

            # Insert into MongoDB with upsert to avoid duplicates
            result = self._insert_transactions(transactions_to_insert)

            return result

        except Exception as e:
            logging.error(f"❌ Error loading transactions: {str(e)}")
            return {"success": False, "message": f"Error loading transactions: {str(e)}"}

    def load_from_excel(self, file_path):
        """
        Loads transactions from an Excel file into MongoDB.
        
        Args:
            file_path (str): Path to the Excel file
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            logging.info(f"Read {len(df)} rows from {file_path}")

            # Check column headers and map to required format
            df = self._map_columns(df)

            # Check for required columns
            required_columns = ["transaction_id", "name", "amount", "date"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                logging.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                return {
                    "success": False,
                    "message": f"Missing required columns: {', '.join(missing_columns)}",
                    "suggestion": "Your file must contain columns for transaction ID, name, amount, and date."
                }

            # Add any missing optional columns
            if "account_id" not in df.columns:
                df["account_id"] = "manual-import"

            if "category" not in df.columns:
                df["category"] = "Uncategorized"

            # Ensure transaction_id is unique
            if df['transaction_id'].duplicated().any():
                # Add a unique suffix to duplicated IDs
                mask = df['transaction_id'].duplicated()
                df.loc[mask, 'transaction_id'] = df.loc[mask, 'transaction_id'] + '_' + [str(uuid.uuid4())[:8] for _ in
                                                                                         range(sum(mask))]

            # Clean data
            df = self._clean_transaction_data(df)

            # Convert to list of dictionaries for MongoDB
            transactions_to_insert = df.to_dict('records')

            # Insert into MongoDB
            result = self._insert_transactions(transactions_to_insert)

            if result["success"]:
                result["preview"] = transactions_to_insert[:5]

            return result

        except pd.errors.EmptyDataError:
            logging.error("❌ The file is empty.")
            return {"success": False, "message": "The file is empty."}
        except pd.errors.ParserError:
            logging.error("❌ Could not parse the file. Make sure it's a valid Excel or CSV file.")
            return {"success": False, "message": "Could not parse the file. Make sure it's a valid Excel or CSV file."}
        except Exception as e:
            logging.error(f"❌ Error loading file: {str(e)}")
            return {"success": False, "message": f"Error loading file: {str(e)}"}

    def _map_columns(self, df):
        """
        Maps common column names to the required format.
        
        Args:
            df (DataFrame): Original DataFrame
            
        Returns:
            DataFrame: DataFrame with standardized column names
        """
        # Create a mapping of common column names to our standard names
        column_mapping = {
            # Transaction ID
            'transaction_id': 'transaction_id',
            'id': 'transaction_id',
            'transaction id': 'transaction_id',
            'txn_id': 'transaction_id',
            'txn id': 'transaction_id',

            # Name/Description
            'name': 'name',
            'description': 'name',
            'merchant': 'name',
            'payee': 'name',
            'transaction': 'name',
            'transaction_name': 'name',

            # Amount
            'amount': 'amount',
            'transaction_amount': 'amount',
            'payment_amount': 'amount',
            'price': 'amount',
            'cost': 'amount',
            'value': 'amount',

            # Date
            'date': 'date',
            'transaction_date': 'date',
            'payment_date': 'date',

            # Category
            'category': 'category',
            'transaction_category': 'category',
            'type': 'category',
            'transaction_type': 'category',

            # Account
            'account_id': 'account_id',
            'account': 'account_id'
        }

        # Normalize the DataFrame column names (lowercase, strip whitespace)
        df.columns = [c.lower().strip() for c in df.columns]

        # Rename columns based on mapping
        for original, standard in column_mapping.items():
            if original in df.columns:
                df.rename(columns={original: standard}, inplace=True)

        # If transaction_id is missing, create it
        if "transaction_id" not in df.columns:
            df["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

        return df

    def _clean_transaction_data(self, df):
        """
        Cleans and standardizes transaction data.
        
        Args:
            df (DataFrame): Original DataFrame
            
        Returns:
            DataFrame: Cleaned DataFrame
        """
        # Make a copy to avoid warnings
        df = df.copy()

        # Convert date to datetime if it's not already
        if df["date"].dtype != 'datetime64[ns]':
            try:
                df["date"] = pd.to_datetime(df["date"])
            except:
                # If conversion fails, try with a common format
                try:
                    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
                except:
                    # If that fails, use today's date and log warning
                    logging.warning("❌ Could not parse dates. Using today's date.")
                    df["date"] = datetime.now()

        # Ensure amount is a float
        if df["amount"].dtype not in ['float64', 'int64']:
            try:
                # Remove currency symbols and commas
                df["amount"] = df["amount"].astype(str).str.replace('$', '').str.replace(',', '')
                df["amount"] = pd.to_numeric(df["amount"], errors='coerce')
            except:
                logging.warning("❌ Could not convert amounts to numbers.")

        # Fill NaN values
        df["amount"].fillna(0, inplace=True)
        df["name"].fillna("Unknown", inplace=True)
        df["category"].fillna("Uncategorized", inplace=True)

        # Convert amount to absolute value (Plaid uses negative for expenses)
        df["amount"] = df["amount"].abs()

        # Convert dates to string in ISO format for MongoDB
        df["date"] = df["date"].dt.strftime('%Y-%m-%d')

        return df

    def _insert_transactions(self, transactions):
        """
        Insert transactions into MongoDB with upsert to avoid duplicates.
        
        Args:
            transactions (list): List of transaction dictionaries
            
        Returns:
            dict: Result of the operation
        """
        try:
            if not transactions:
                return {"success": False, "message": "No transactions to insert"}

            inserted_count = 0
            updated_count = 0

            for transaction in transactions:
                # Try to insert or update based on transaction_id
                result = self.transactions_collection.update_one(
                    {"transaction_id": transaction["transaction_id"]},
                    {"$set": transaction},
                    upsert=True
                )

                if result.upserted_id:
                    inserted_count += 1
                elif result.modified_count:
                    updated_count += 1

            total_processed = len(transactions)
            logging.info(
                f"✅ Processed {total_processed} transactions: {inserted_count} inserted, {updated_count} updated")

            return {
                "success": True,
                "message": f"Successfully processed {total_processed} transactions.",
                "count": total_processed,
                "inserted": inserted_count,
                "updated": updated_count
            }

        except Exception as e:
            logging.error(f"❌ MongoDB insertion error: {str(e)}")
            return {"success": False, "message": f"Failed to insert transactions: {str(e)}"}
