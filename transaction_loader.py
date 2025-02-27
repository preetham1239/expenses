import pandas as pd
from sqlalchemy.exc import IntegrityError
from database import get_engine


class TransactionLoader:
    """Loads transactions into the database from Plaid or Excel."""

    def __init__(self):
        self.engine = get_engine()

    def load_from_plaid(self, transactions):
        """Loads transactions from Plaid API response into the database."""
        if not transactions:
            print("No transactions to load.")
            return

        df = pd.DataFrame(transactions)
        df = df.rename(columns={"transaction_id": "transaction_id", "account_id": "account_id", "name": "name",
                                "amount": "amount", "date": "date", "category": "category"})
        df = df[["transaction_id", "account_id", "name", "amount", "date", "category"]]

        try:
            df.to_sql("transactions", self.engine, if_exists="append", index=False)
            print("✅ Transactions loaded successfully.")
        except IntegrityError:
            print("❌ Some transactions already exist.")

    def load_from_excel(self, file_path):
        """Loads transactions from an Excel file into the database."""
        df = pd.read_excel(file_path)

        required_columns = {"transaction_id", "account_id", "name", "amount", "date", "category"}
        if not required_columns.issubset(set(df.columns)):
            print("❌ Invalid file format. Required columns missing.")
            return

        try:
            df.to_sql("transactions", self.engine, if_exists="append", index=False)
            print("✅ Transactions loaded successfully from Excel.")
        except IntegrityError:
            print("❌ Some transactions already exist.")
