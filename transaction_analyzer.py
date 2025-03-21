# transaction_analyzer.py
import pandas as pd
import logging
from datetime import datetime
from mongodb_client import get_database


class TransactionAnalyzer:
    """Analyzes transaction data and generates insights using MongoDB."""

    def __init__(self):
        self.db = get_database()
        self.transactions_collection = self.db['transactions']

    def spending_by_category(self, start_date=None, end_date=None):
        """
        Analyze spending by category.
        
        Args:
            start_date (str, optional): Filter by start date (YYYY-MM-DD)
            end_date (str, optional): Filter by end date (YYYY-MM-DD)
            
        Returns:
            dict: Category spending data and statistics
        """
        try:
            # Build the query with optional date filtering
            query = {}

            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["date"] = date_query

            # MongoDB aggregation pipeline
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$category",
                    "total_amount": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"total_amount": -1}}
            ]

            # Execute the aggregation
            result = list(self.transactions_collection.aggregate(pipeline))

            # Convert to DataFrame for easier processing
            if result:
                df = pd.DataFrame(result)
                df.rename(columns={"_id": "category"}, inplace=True)

                # Calculate percentages
                total_spending = df['total_amount'].sum()
                df['percentage'] = (df['total_amount'] / total_spending * 100).round(2)

                # Convert to list of dictionaries for JSON response
                categories = df.to_dict('records')

                # Calculate summary statistics
                summary = {
                    "total_spending": float(total_spending),
                    "category_count": len(categories),
                    "top_category": categories[0]['category'] if categories else None,
                    "top_category_percentage": float(categories[0]['percentage']) if categories else None
                }

                return {
                    "categories": categories,
                    "summary": summary
                }
            else:
                return {
                    "categories": [],
                    "summary": {
                        "total_spending": 0,
                        "category_count": 0,
                        "top_category": None,
                        "top_category_percentage": None
                    }
                }
        except Exception as e:
            logging.error(f"❌ Error analyzing spending by category: {str(e)}")
            raise

    def monthly_spending_trend(self, year=None):
        """
        Analyze monthly spending trends.
        
        Args:
            year (str, optional): Filter by year (YYYY)
            
        Returns:
            dict: Monthly spending data and statistics
        """
        try:
            # Build the query with optional year filtering
            query = {}
            if year:
                # Add regex filter for year
                query["date"] = {"$regex": f"^{year}"}

            # MongoDB aggregation pipeline to extract year and month
            pipeline = [
                {"$match": query},
                {"$addFields": {
                    "year": {"$substr": ["$date", 0, 4]},
                    "month": {"$substr": ["$date", 5, 2]}
                }},
                {"$group": {
                    "_id": {
                        "year": "$year",
                        "month": "$month"
                    },
                    "total_amount": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]

            # Execute the aggregation
            result = list(self.transactions_collection.aggregate(pipeline))

            # Convert to more usable format
            monthly_data = []
            for item in result:
                monthly_data.append({
                    "year": item["_id"]["year"],
                    "month": int(item["_id"]["month"]),
                    "total_amount": item["total_amount"],
                    "transaction_count": item["transaction_count"]
                })

            # Convert to DataFrame for easier processing
            if monthly_data:
                df = pd.DataFrame(monthly_data)

                # Create month names
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December']

                # Add month name
                df['month_name'] = df['month'].apply(lambda x: month_names[int(x)-1])

                # Calculate month-over-month change
                df = df.sort_values(by=['year', 'month'])
                df['previous_month'] = df['total_amount'].shift(1)
                df['mom_change'] = ((df['total_amount'] - df['previous_month']) /
                                    df['previous_month'] * 100).round(2)

                # Convert to list of dictionaries for JSON response
                monthly_data = df.fillna(0).to_dict('records')

                # Calculate summary statistics
                summary = {
                    "average_monthly_spending": float(df['total_amount'].mean()),
                    "highest_spending_month": df.loc[df['total_amount'].idxmax()]['month_name'],
                    "lowest_spending_month": df.loc[df['total_amount'].idxmin()]['month_name'],
                    "total_annual_spending": float(df['total_amount'].sum())
                }

                return {
                    "monthly_data": monthly_data,
                    "summary": summary
                }
            else:
                return {
                    "monthly_data": [],
                    "summary": {
                        "average_monthly_spending": 0,
                        "highest_spending_month": None,
                        "lowest_spending_month": None,
                        "total_annual_spending": 0
                    }
                }
        except Exception as e:
            logging.error(f"❌ Error analyzing monthly trends: {str(e)}")
            raise

    def top_merchants(self, limit=10, start_date=None, end_date=None):
        """
        Get top merchants by spending amount.
        
        Args:
            limit (int): Number of merchants to return
            start_date (str, optional): Filter by start date (YYYY-MM-DD)
            end_date (str, optional): Filter by end date (YYYY-MM-DD)
            
        Returns:
            dict: Top merchants data
        """
        try:
            # Build the query with optional date filtering
            query = {}

            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["date"] = date_query

            # MongoDB aggregation pipeline
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$name",
                    "total_amount": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1},
                    "average_transaction": {"$avg": "$amount"},
                    "first_transaction": {"$min": "$date"},
                    "last_transaction": {"$max": "$date"}
                }},
                {"$sort": {"total_amount": -1}},
                {"$limit": limit}
            ]

            # Execute the aggregation
            result = list(self.transactions_collection.aggregate(pipeline))

            # Format result
            merchants = []
            for item in result:
                merchants.append({
                    "merchant_name": item["_id"],
                    "total_amount": item["total_amount"],
                    "transaction_count": item["transaction_count"],
                    "average_transaction": round(item["average_transaction"], 2),
                    "first_transaction": item["first_transaction"],
                    "last_transaction": item["last_transaction"]
                })

            # Get overall date range from the database
            date_range = {"start": start_date, "end": end_date}
            if not start_date or not end_date:
                # Only query for the missing dates
                date_pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": None,
                        "min_date": {"$min": "$date"},
                        "max_date": {"$max": "$date"}
                    }}
                ]
                date_result = list(self.transactions_collection.aggregate(date_pipeline))

                if date_result:
                    if not start_date:
                        date_range["start"] = date_result[0]["min_date"]
                    if not end_date:
                        date_range["end"] = date_result[0]["max_date"]

            return {
                "top_merchants": merchants,
                "total_count": len(merchants),
                "date_range": date_range
            }
        except Exception as e:
            logging.error(f"❌ Error analyzing top merchants: {str(e)}")
            raise
