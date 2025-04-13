from datetime import datetime, date
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
        self.account_id = data.get('account_id')
        self.name = data.get('name')
        self.merchant_name = data.get('merchant_name')
        self.amount = data.get('amount')
        self.date = data.get('date')
        self.category = None
        self.currency = data.get('iso_currency_code', 'USD')

        # Store a serializable version of the original data (handles nested date/datetime objects)
        self.original_data = Transaction.make_serializable(data)

    @staticmethod
    def default_serializer(obj):
        """
        Custom serializer for non-serializable types.
        Converts date and datetime objects to their ISO formatted string.
        """
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def make_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a dictionary to a serializable format using the custom default_serializer.
        This ensures any date or datetime objects, even nested ones, are converted to strings.
        """
        if data is None:
            return {}
        json_str = json.dumps(data, default=Transaction.default_serializer)
        return json.loads(json_str)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Transaction to a dictionary for database storage.
        Ensures that any date/datetime in the 'date' field is converted to a string.
        """
        date_value = (
            self.date.isoformat() if isinstance(self.date, (date, datetime)) else self.date
        )
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "name": self.name,
            "merchant": self.merchant_name,
            "amount": self.amount,
            "date": date_value,
            "category": self.category,
            "iso_currency_code": self.currency,
            "original_data": self.original_data,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }

    def to_json(self) -> str:
        """
        Convert this Transaction instance to a JSON string.
        The default_serializer is used here as well to catch any non-serializable types.
        """
        return json.dumps(self.to_dict(), default=Transaction.default_serializer)

    def __repr__(self) -> str:
        """
        String representation of the Transaction.
        """
        return (
            f"Transaction(id={self.transaction_id}, name={self.name}, "
            f"amount={self.amount}, date={self.date})"
        )
