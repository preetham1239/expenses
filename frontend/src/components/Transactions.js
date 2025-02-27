import React, { useState } from "react";
import axios from "axios";

const Transactions = ({ accessToken }) => {
    const [transactions, setTransactions] = useState([]);

    const fetchTransactions = async () => {
        const response = await axios.post("https://localhost:8000/transactions/get", {
            access_token: accessToken,
        });
        setTransactions(response.data.transactions);
    };

    return (
        <div>
            <h2>Your Transactions</h2>
            <button onClick={fetchTransactions}>Fetch Transactions</button>
            <ul>
                {transactions.map((txn) => (
                    <li key={txn.transaction_id}>
                        {txn.date} - {txn.name}: ${txn.amount}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Transactions;
