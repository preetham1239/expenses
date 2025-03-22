import React, { useState, useEffect } from "react";
import axios from "axios";
import TransactionDetailPopup from "./TransactionDetailPopup";
import TransactionEditForm from "./TransactionEditForm";

const Transactions = ({ accessToken }) => {
    const [transactions, setTransactions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isFirstLoad, setIsFirstLoad] = useState(true);
    const [dateRange, setDateRange] = useState({
        startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0], // 30 days ago
        endDate: new Date().toISOString().split('T')[0] // Today
    });
    const [selectedTransaction, setSelectedTransaction] = useState(null);
    const [isEditFormOpen, setIsEditFormOpen] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(null);

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(20);
    const [totalTransactions, setTotalTransactions] = useState(0);
    const [displayedTransactions, setDisplayedTransactions] = useState([]);

    // In your Transactions.js component, update the fetchTransactions function

    const fetchTransactions = async () => {
        setIsLoading(true);
        setError(null);

        // Reset pagination when fetching new data
        setCurrentPage(1);

        // Log the date range for debugging
        console.log("Fetching transactions with date range:", dateRange);

        try {
            // Try to fetch from the new DB endpoint first
            let response;
            try {
                // First try the direct DB endpoint which should return all transactions
                response = await axios.post("https://localhost:8000/transactions/get-from-db", {
                    start_date: dateRange.startDate,
                    end_date: dateRange.endDate,
                    limit: 2000 // Request a high limit
                }, {
                    withCredentials: true
                });
                console.log("Using direct DB endpoint for transactions");
            } catch (dbErr) {
                console.log("Direct DB endpoint failed, falling back to Plaid API", dbErr);
                // Fall back to the Plaid API endpoint
                response = await axios.post("https://localhost:8000/transactions/get", {
                    access_token: accessToken,
                    start_date: dateRange.startDate,
                    end_date: dateRange.endDate,
                    limit: 1000 // Request a high limit from Plaid API
                }, {
                    withCredentials: true
                });
            }

            if (response.data.transactions) {
                const txns = response.data.transactions;
                console.log(`Received ${txns.length} transactions from API`);

                // Debug: examine date range of received transactions
                if (txns.length > 0) {
                    const dates = txns.map(t => t.date).sort();
                    console.log(`Transaction date range: ${dates[0]} to ${dates[dates.length-1]}`);
                    console.log(`First 5 dates: ${dates.slice(0, 5).join(', ')}`);
                    console.log(`Last 5 dates: ${dates.slice(-5).join(', ')}`);
                }

                // Display additional information if available
                if (response.data.total_count) {
                    console.log(`Total matching transactions: ${response.data.total_count}`);
                    console.log(`Returned transactions: ${response.data.returned_count}`);
                }

                // Store all transactions
                setTransactions(txns);
                setTotalTransactions(txns.length);

                // Update the displayed transactions based on current page
                updateDisplayedTransactions(txns, 1);
            } else {
                setError("No transactions found");
                setTransactions([]);
                setDisplayedTransactions([]);
                setTotalTransactions(0);
            }
        } catch (err) {
            console.error("Error fetching transactions:", err);
            let errorMessage = "Failed to fetch transactions. Please try again.";

            if (err.response && err.response.data && err.response.data.error) {
                errorMessage = err.response.data.error;
            }

            setError(errorMessage);
            setTransactions([]);
            setDisplayedTransactions([]);
            setTotalTransactions(0);
        } finally {
            setIsLoading(false);
        }
    };

    // Function to update displayed transactions based on pagination
    const updateDisplayedTransactions = (txns, page) => {
        const startIndex = (page - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedTransactions = txns.slice(startIndex, endIndex);
        setDisplayedTransactions(paginatedTransactions);
        console.log(`Displaying ${paginatedTransactions.length} transactions (page ${page} of ${Math.ceil(txns.length/itemsPerPage)})`);
    };

    // Handle page change
    const handlePageChange = (newPage) => {
        setCurrentPage(newPage);
        updateDisplayedTransactions(transactions, newPage);

        // Scroll to top of transaction list
        document.getElementById('transaction-table-container').scrollTop = 0;
    };

    // Handle items per page change
    const handleItemsPerPageChange = (e) => {
        const newItemsPerPage = parseInt(e.target.value);
        setItemsPerPage(newItemsPerPage);
        setCurrentPage(1); // Reset to first page
        updateDisplayedTransactions(transactions, 1);
    };

    // Automatically fetch transactions when component mounts
    useEffect(() => {
        if (isFirstLoad) {
            fetchTransactions();
            setIsFirstLoad(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isFirstLoad]);

    // Update displayed transactions when current page or items per page changes
    useEffect(() => {
        if (transactions.length > 0) {
            updateDisplayedTransactions(transactions, currentPage);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentPage, itemsPerPage]);

    // Handle date change
    const handleDateChange = (e) => {
        const { name, value } = e.target;
        setDateRange(prev => ({
            ...prev,
            [name]: value
        }));
    };

    // Handle showing the detail popup
    const handleShowDetails = (transaction) => {
        setSelectedTransaction(transaction);
    };

    // Handle showing the edit form
    const handleEditTransaction = (transaction) => {
        setSelectedTransaction(transaction);
        setIsEditFormOpen(true);
    };

    // Handle saving the edited transaction
    const handleSaveTransaction = async (updatedTransaction) => {
        try {
            // In a real app, you would make an API call here
            // For this example, we'll just update the local state

            // Mock API call - replace with real API call in production
            // const response = await axios.put("https://localhost:8000/transactions/update", {
            //     transaction_id: updatedTransaction.transaction_id,
            //     name: updatedTransaction.name,
            //     amount: updatedTransaction.amount,
            //     date: updatedTransaction.date,
            //     category: updatedTransaction.category
            // }, {
            //     withCredentials: true
            // });

            // Update the transaction in the local state (both full list and displayed list)
            const updatedTransactions = transactions.map(txn =>
                txn.transaction_id === updatedTransaction.transaction_id ? updatedTransaction : txn
            );

            setTransactions(updatedTransactions);

            const updatedDisplayedTransactions = displayedTransactions.map(txn =>
                txn.transaction_id === updatedTransaction.transaction_id ? updatedTransaction : txn
            );

            setDisplayedTransactions(updatedDisplayedTransactions);

            setIsEditFormOpen(false);
            setSelectedTransaction(null);

            // Show success message
            setSaveSuccess("Transaction updated successfully");
            setTimeout(() => setSaveSuccess(null), 3000);

            return true;
        } catch (err) {
            console.error("Error updating transaction:", err);
            throw new Error("Failed to update transaction");
        }
    };

    // Close any popups
    const handleClosePopup = () => {
        setSelectedTransaction(null);
        setIsEditFormOpen(false);
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

    // Generate page numbers for pagination
    const generatePageNumbers = () => {
        const totalPages = Math.ceil(totalTransactions / itemsPerPage);
        const pages = [];

        // For small number of pages, show all
        if (totalPages <= 7) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // For large number of pages, show first, last, and pages around current
            if (currentPage <= 3) {
                // Near the beginning
                for (let i = 1; i <= 5; i++) {
                    pages.push(i);
                }
                pages.push("...");
                pages.push(totalPages);
            } else if (currentPage >= totalPages - 2) {
                // Near the end
                pages.push(1);
                pages.push("...");
                for (let i = totalPages - 4; i <= totalPages; i++) {
                    pages.push(i);
                }
            } else {
                // Middle
                pages.push(1);
                pages.push("...");
                for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                    pages.push(i);
                }
                pages.push("...");
                pages.push(totalPages);
            }
        }

        return pages;
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

            {saveSuccess && (
                <div style={{
                    backgroundColor: "#e8f5e9",
                    color: "#2e7d32",
                    padding: "10px",
                    borderRadius: "4px",
                    marginBottom: "15px"
                }}>
                    <p style={{ margin: 0 }}><strong>Success:</strong> {saveSuccess}</p>
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

            {/* Transactions Count */}
            {totalTransactions > 0 && (
                <div style={{ marginBottom: "15px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <strong>Total:</strong> {totalTransactions} transactions
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <label htmlFor="itemsPerPage" style={{ marginRight: "10px" }}>Items per page:</label>
                        <select
                            id="itemsPerPage"
                            value={itemsPerPage}
                            onChange={handleItemsPerPageChange}
                            style={{
                                padding: "5px",
                                borderRadius: "4px",
                                border: "1px solid #ccc"
                            }}
                        >
                            <option value="10">10</option>
                            <option value="20">20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select>
                    </div>
                </div>
            )}

            {isLoading ? (
                <div style={{ textAlign: "center", padding: "30px" }}>
                    <p>Loading your transactions...</p>
                </div>
            ) : totalTransactions > 0 ? (
                <div>
                    <div
                        id="transaction-table-container"
                        style={{
                            overflowX: "auto",
                            maxHeight: "600px",
                            overflowY: "auto",
                            marginBottom: "20px"
                        }}
                    >
                        <table style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
                        }}>
                            <thead style={{ position: "sticky", top: 0, backgroundColor: "#f2f2f2", zIndex: 1 }}>
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
                                <th style={{
                                    textAlign: "center",
                                    padding: "12px",
                                    backgroundColor: "#f2f2f2",
                                    borderBottom: "2px solid #ddd"
                                }}>Actions</th>
                            </tr>
                            </thead>
                            <tbody>
                            {displayedTransactions.map((txn) => (
                                <tr
                                    key={txn.transaction_id}
                                    style={{
                                        borderBottom: "1px solid #ddd",
                                        cursor: "pointer"
                                    }}
                                    onClick={() => handleShowDetails(txn)}
                                >
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
                                    <td style={{
                                        padding: "10px",
                                        textAlign: "center"
                                    }}>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation(); // Prevent row click
                                                handleEditTransaction(txn);
                                            }}
                                            style={{
                                                padding: "5px 10px",
                                                backgroundColor: "#2196F3",
                                                color: "white",
                                                border: "none",
                                                borderRadius: "4px",
                                                cursor: "pointer"
                                            }}
                                        >
                                            Edit
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    {totalTransactions > itemsPerPage && (
                        <div style={{
                            display: "flex",
                            justifyContent: "center",
                            marginTop: "20px",
                            alignItems: "center"
                        }}>
                            <button
                                onClick={() => handlePageChange(1)}
                                disabled={currentPage === 1}
                                style={{
                                    padding: "5px 10px",
                                    margin: "0 5px",
                                    backgroundColor: currentPage === 1 ? "#f0f0f0" : "#f8f8f8",
                                    border: "1px solid #ddd",
                                    borderRadius: "4px",
                                    cursor: currentPage === 1 ? "not-allowed" : "pointer",
                                    opacity: currentPage === 1 ? 0.6 : 1
                                }}
                            >
                                ⟪ First
                            </button>

                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                style={{
                                    padding: "5px 10px",
                                    margin: "0 5px",
                                    backgroundColor: currentPage === 1 ? "#f0f0f0" : "#f8f8f8",
                                    border: "1px solid #ddd",
                                    borderRadius: "4px",
                                    cursor: currentPage === 1 ? "not-allowed" : "pointer",
                                    opacity: currentPage === 1 ? 0.6 : 1
                                }}
                            >
                                ← Prev
                            </button>

                            <div style={{
                                display: "flex",
                                margin: "0 10px"
                            }}>
                                {generatePageNumbers().map((page, index) => (
                                    page === "..." ? (
                                        <span
                                            key={`ellipsis-${index}`}
                                            style={{
                                                padding: "5px 10px",
                                                margin: "0 2px"
                                            }}
                                        >
                                            {page}
                                        </span>
                                    ) : (
                                        <button
                                            key={page}
                                            onClick={() => handlePageChange(page)}
                                            style={{
                                                padding: "5px 10px",
                                                margin: "0 2px",
                                                backgroundColor: currentPage === page ? "#2196F3" : "#f8f8f8",
                                                color: currentPage === page ? "white" : "black",
                                                border: "1px solid #ddd",
                                                borderRadius: "4px",
                                                cursor: "pointer"
                                            }}
                                        >
                                            {page}
                                        </button>
                                    )
                                ))}
                            </div>

                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === Math.ceil(totalTransactions / itemsPerPage)}
                                style={{
                                    padding: "5px 10px",
                                    margin: "0 5px",
                                    backgroundColor: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? "#f0f0f0" : "#f8f8f8",
                                    border: "1px solid #ddd",
                                    borderRadius: "4px",
                                    cursor: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? "not-allowed" : "pointer",
                                    opacity: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? 0.6 : 1
                                }}
                            >
                                Next →
                            </button>

                            <button
                                onClick={() => handlePageChange(Math.ceil(totalTransactions / itemsPerPage))}
                                disabled={currentPage === Math.ceil(totalTransactions / itemsPerPage)}
                                style={{
                                    padding: "5px 10px",
                                    margin: "0 5px",
                                    backgroundColor: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? "#f0f0f0" : "#f8f8f8",
                                    border: "1px solid #ddd",
                                    borderRadius: "4px",
                                    cursor: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? "not-allowed" : "pointer",
                                    opacity: currentPage === Math.ceil(totalTransactions / itemsPerPage) ? 0.6 : 1
                                }}
                            >
                                Last ⟫
                            </button>
                        </div>
                    )}
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

            {/* Transaction Detail Popup */}
            {selectedTransaction && !isEditFormOpen && (
                <TransactionDetailPopup
                    transaction={selectedTransaction}
                    onClose={handleClosePopup}
                    onEdit={handleEditTransaction}
                />
            )}

            {/* Transaction Edit Form */}
            {selectedTransaction && isEditFormOpen && (
                <TransactionEditForm
                    transaction={selectedTransaction}
                    onClose={handleClosePopup}
                    onSave={handleSaveTransaction}
                />
            )}
        </div>
    );
};

export default Transactions;
