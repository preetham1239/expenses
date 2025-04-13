from datetime import datetime
from typing import Dict, Any
import json


class Transaction:
    """
    Unified transaction model that can handle data from different sources (Plaid, CSV, etc.)
    and provides a consistent interface for the application.
    """

    def __init__(self, data: Dict[str, Any] = None):
        """
        Initialize a transaction from a dictionary of attributes.
        If a field is missing, a sensible default will be used.

        Args:
            data (Dict[str, Any], optional): Dictionary containing transaction data
        """
        data = data or {}

        self.transaction_id = data.get('transaction_id')
        self.account_id = data.get('account_id', '')
        self.name = data.get('name', '')
        self.merchant_name = data.get('merchant_name')
        self.amount = data.get('amount')
        self.date = data.get('authorized_date').isoformat()
        self.category = data.get('category')
        self.currency = data.get('iso_currency_code', 'USD')
        self.original_data = Transaction.dict_to_json(data.copy())

    def to_dict(self) -> Dict[str, Any]:
        """Convert Transaction to a dictionary for database storage."""
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "name": self.name,
            "merchant": self.merchant_name,
            "amount": self.amount,
            "date": self.date,
            "category": self.category,
            "iso_currency_code": self.currency,
            "original_data": self.original_data,
            "last_updated": datetime.now().isoformat()
        }

    def to_json(self) -> str:
        """Convert this Transaction instance to a JSON string."""
        # Convert instance to dict first, then to JSON
        return json.dumps(self.to_dict())

    @staticmethod
    def dict_to_json(data: Dict[str, Any]) -> str:
        """Convert a dictionary to a JSON string."""
        return json.dumps(data)

    def __repr__(self) -> str:
        """String representation of the Transaction."""
        return f"Transaction(id={self.transaction_id}, name={self.name}, amount={self.amount}, date={self.date})"
