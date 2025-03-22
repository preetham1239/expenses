import React, { useState, useEffect } from "react";
import axios from "axios";

const Transactions = ({ accessToken }) => {
    const [transactions, setTransactions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isFirstLoad, setIsFirstLoad] = useState(true);
    const [dateRange, setDateRange] = useState({
        startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0], // 30 days ago
        endDate: new Date().toISOString().split('T')[0] // Today
    });

    const fetchTransactions = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await axios.post("https://localhost:8000/transactions/get", {
                access_token: accessToken, // This might be null if we're using the DB token
                start_date: dateRange.startDate,
                end_date: dateRange.endDate
            }, {
                withCredentials: true
            });

            if (response.data.transactions) {
                setTransactions(response.data.transactions);
            } else {
                setError("No transactions found");
            }
        } catch (err) {
            console.error("Error fetching transactions:", err);
            let errorMessage = "Failed to fetch transactions. Please try again.";

            if (err.response && err.response.data && err.response.data.error) {
                errorMessage = err.response.data.error;
            }

            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // Automatically fetch transactions when component mounts
    useEffect(() => {
        if (isFirstLoad) {
            fetchTransactions();
            setIsFirstLoad(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isFirstLoad]);

    // Handle date change
    const handleDateChange = (e) => {
        const { name, value } = e.target;
        setDateRange(prev => ({
            ...prev,
            [name]: value
        }));
    };

    // Format date for display
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    };

    // Format currency
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    return (
        <div style={{ padding: "20px" }}>
            <h2>Your Transactions</h2>

            {error && (
                <div style={{
                    backgroundColor: "#ffebee",
                    color: "#c62828",
                    padding: "10px",
                    borderRadius: "4px",
                    marginBottom: "15px"
                }}>
                    <p style={{ margin: 0 }}><strong>Error:</strong> {error}</p>
                </div>
            )}

            <div style={{ display: "flex", gap: "15px", marginBottom: "20px", flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                    <label htmlFor="startDate" style={{ display: "block", marginBottom: "5px" }}>
                        Start Date:
                    </label>
                    <input
                        type="date"
                        id="startDate"
                        name="startDate"
                        value={dateRange.startDate}
                        onChange={handleDateChange}
                        style={{
                            padding: "8px",
                            borderRadius: "4px",
                            border: "1px solid #ccc"
                        }}
                    />
                </div>

                <div>
                    <label htmlFor="endDate" style={{ display: "block", marginBottom: "5px" }}>
                        End Date:
                    </label>
                    <input
                        type="date"
                        id="endDate"
                        name="endDate"
                        value={dateRange.endDate}
                        onChange={handleDateChange}
                        style={{
                            padding: "8px",
                            borderRadius: "4px",
                            border: "1px solid #ccc"
                        }}
                    />
                </div>

                <button
                    onClick={fetchTransactions}
                    disabled={isLoading}
                    style={{
                        padding: "10px 15px",
                        backgroundColor: isLoading ? "#cccccc" : "#2196F3",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: isLoading ? "not-allowed" : "pointer"
                    }}
                >
                    {isLoading ? "Loading..." : "Refresh Transactions"}
                </button>
            </div>

            {isLoading ? (
                <div style={{ textAlign: "center", padding: "30px" }}>
                    <p>Loading your transactions...</p>
                </div>
            ) : transactions.length > 0 ? (
                <div style={{ overflowX: "auto" }}>
                    <table style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
                    }}>
                        <thead>
                        <tr>
                            <th style={{
                                textAlign: "left",
                                padding: "12px",
                                backgroundColor: "#f2f2f2",
                                borderBottom: "2px solid #ddd"
                            }}>Date</th>
                            <th style={{
                                textAlign: "left",
                                padding: "12px",
                                backgroundColor: "#f2f2f2",
                                borderBottom: "2px solid #ddd"
                            }}>Description</th>
                            <th style={{
                                textAlign: "right",
                                padding: "12px",
                                backgroundColor: "#f2f2f2",
                                borderBottom: "2px solid #ddd"
                            }}>Amount</th>
                            <th style={{
                                textAlign: "left",
                                padding: "12px",
                                backgroundColor: "#f2f2f2",
                                borderBottom: "2px solid #ddd"
                            }}>Category</th>
                        </tr>
                        </thead>
                        <tbody>
                        {transactions.map((txn) => (
                            <tr key={txn.transaction_id} style={{ borderBottom: "1px solid #ddd" }}>
                                <td style={{ padding: "10px" }}>{formatDate(txn.date)}</td>
                                <td style={{ padding: "10px" }}>{txn.name}</td>
                                <td style={{
                                    padding: "10px",
                                    textAlign: "right",
                                    color: parseFloat(txn.amount) < 0 ? "#c62828" : "#2e7d32"
                                }}>
                                    {formatCurrency(txn.amount)}
                                </td>
                                <td style={{ padding: "10px" }}>
                                    {Array.isArray(txn.category) ? txn.category[0] : txn.category || "Uncategorized"}
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div style={{
                    textAlign: "center",
                    padding: "30px",
                    backgroundColor: "#f5f5f5",
                    borderRadius: "4px"
                }}>
                    <p>No transactions found. Please adjust the date range or try refreshing.</p>
                </div>
            )}
        </div>
    );
};

export default Transactions;
