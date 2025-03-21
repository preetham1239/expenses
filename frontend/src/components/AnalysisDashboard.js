import React, { useState, useEffect } from "react";
import axios from "axios";

const AnalysisDashboard = () => {
    const [categoryData, setCategoryData] = useState(null);
    const [monthlyData, setMonthlyData] = useState(null);
    const [merchantData, setMerchantData] = useState(null);
    const [loading, setLoading] = useState({
        categories: false,
        monthly: false,
        merchants: false
    });
    const [error, setError] = useState({
        categories: null,
        monthly: null,
        merchants: null
    });
    const [dateRange, setDateRange] = useState({
        startDate: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0], // Jan 1 of current year
        endDate: new Date().toISOString().split('T')[0], // Today
        year: new Date().getFullYear().toString()
    });

    // Fetch category spending data
    const fetchCategoryData = async () => {
        setLoading(prev => ({ ...prev, categories: true }));
        setError(prev => ({ ...prev, categories: null }));

        try {
            const response = await axios.get("https://localhost:8000/analysis/spending-by-category", {
                params: {
                    start_date: dateRange.startDate,
                    end_date: dateRange.endDate
                },
                withCredentials: true
            });

            setCategoryData(response.data);
        } catch (err) {
            console.error("Error fetching category data:", err);
            setError(prev => ({
                ...prev,
                categories: err.response?.data?.error || "Failed to fetch category data"
            }));
        } finally {
            setLoading(prev => ({ ...prev, categories: false }));
        }
    };

    // Fetch monthly trend data
    const fetchMonthlyData = async () => {
        setLoading(prev => ({ ...prev, monthly: true }));
        setError(prev => ({ ...prev, monthly: null }));

        try {
            const response = await axios.get("https://localhost:8000/analysis/monthly-trend", {
                params: {
                    year: dateRange.year
                },
                withCredentials: true
            });

            setMonthlyData(response.data);
        } catch (err) {
            console.error("Error fetching monthly data:", err);
            setError(prev => ({
                ...prev,
                monthly: err.response?.data?.error || "Failed to fetch monthly data"
            }));
        } finally {
            setLoading(prev => ({ ...prev, monthly: false }));
        }
    };

    // Fetch top merchants data
    const fetchMerchantData = async () => {
        setLoading(prev => ({ ...prev, merchants: true }));
        setError(prev => ({ ...prev, merchants: null }));

        try {
            const response = await axios.get("https://localhost:8000/analysis/top-merchants", {
                params: {
                    start_date: dateRange.startDate,
                    end_date: dateRange.endDate,
                    limit: 10
                },
                withCredentials: true
            });

            setMerchantData(response.data);
        } catch (err) {
            console.error("Error fetching merchant data:", err);
            setError(prev => ({
                ...prev,
                merchants: err.response?.data?.error || "Failed to fetch merchant data"
            }));
        } finally {
            setLoading(prev => ({ ...prev, merchants: false }));
        }
    };

    // Handle date range change
    const handleDateChange = (e) => {
        const { name, value } = e.target;
        setDateRange(prev => ({
            ...prev,
            [name]: value
        }));
    };

    // Initial data fetch
    useEffect(() => {
        fetchCategoryData();
        fetchMonthlyData();
        fetchMerchantData();
    }, []);

    // Refresh data based on filters
    const handleRefresh = () => {
        fetchCategoryData();
        fetchMonthlyData();
        fetchMerchantData();
    };

    // Format currency
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    return (
        <div className="analysis-dashboard" style={{ padding: "20px" }}>
            <h2>Expense Analysis Dashboard</h2>

            {/* Date Range Filters */}
            <div style={{
                display: "flex",
                gap: "15px",
                marginBottom: "20px",
                flexWrap: "wrap",
                alignItems: "flex-end"
            }}>
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

                <div>
                    <label htmlFor="year" style={{ display: "block", marginBottom: "5px" }}>
                        Year (for Monthly Trends):
                    </label>
                    <select
                        id="year"
                        name="year"
                        value={dateRange.year}
                        onChange={handleDateChange}
                        style={{
                            padding: "8px",
                            borderRadius: "4px",
                            border: "1px solid #ccc"
                        }}
                    >
                        <option value="2024">2024</option>
                        <option value="2023">2023</option>
                        <option value="2022">2022</option>
                    </select>
                </div>

                <button
                    onClick={handleRefresh}
                    style={{
                        padding: "8px 15px",
                        backgroundColor: "#2196F3",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Refresh Data
                </button>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "20px" }}>
                {/* Category Spending Section */}
                <div style={{
                    flex: "1 1 400px",
                    backgroundColor: "white",
                    borderRadius: "8px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    padding: "20px"
                }}>
                    <h3>Spending by Category</h3>

                    {loading.categories && (
                        <div>Loading category data...</div>
                    )}

                    {error.categories && (
                        <div style={{ color: "red" }}>{error.categories}</div>
                    )}

                    {categoryData && !loading.categories && (
                        <>
                            {categoryData.summary && (
                                <div style={{
                                    backgroundColor: "#f8f9fa",
                                    padding: "15px",
                                    borderRadius: "4px",
                                    marginBottom: "15px"
                                }}>
                                    <h4 style={{ margin: "0 0 10px 0" }}>Summary</h4>
                                    <p>
                                        <strong>Total Spending:</strong> {formatCurrency(categoryData.summary.total_spending)}
                                    </p>
                                    <p>
                                        <strong>Top Category:</strong> {categoryData.summary.top_category}
                                        ({categoryData.summary.top_category_percentage}%)
                                    </p>
                                    <p>
                                        <strong>Number of Categories:</strong> {categoryData.summary.category_count}
                                    </p>
                                </div>
                            )}

                            {categoryData.categories && categoryData.categories.length > 0 ? (
                                <div style={{ overflowX: "auto" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                        <tr>
                                            <th style={{ textAlign: "left", padding: "8px", borderBottom: "2px solid #ddd" }}>Category</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Amount</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Percentage</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {categoryData.categories.map((category, index) => (
                                            <tr key={index}>
                                                <td style={{ padding: "8px", borderBottom: "1px solid #ddd" }}>{category.category}</td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {formatCurrency(category.total_amount)}
                                                </td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {category.percentage}%
                                                    <div style={{
                                                        width: `${category.percentage}%`,
                                                        height: "4px",
                                                        backgroundColor: "#2196F3",
                                                        marginTop: "4px"
                                                    }}></div>
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p>No category data available.</p>
                            )}
                        </>
                    )}
                </div>

                {/* Monthly Trends Section */}
                <div style={{
                    flex: "1 1 400px",
                    backgroundColor: "white",
                    borderRadius: "8px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    padding: "20px"
                }}>
                    <h3>Monthly Spending Trends</h3>

                    {loading.monthly && (
                        <div>Loading monthly data...</div>
                    )}

                    {error.monthly && (
                        <div style={{ color: "red" }}>{error.monthly}</div>
                    )}

                    {monthlyData && !loading.monthly && (
                        <>
                            {monthlyData.summary && (
                                <div style={{
                                    backgroundColor: "#f8f9fa",
                                    padding: "15px",
                                    borderRadius: "4px",
                                    marginBottom: "15px"
                                }}>
                                    <h4 style={{ margin: "0 0 10px 0" }}>Summary</h4>
                                    <p>
                                        <strong>Average Monthly Spending:</strong> {formatCurrency(monthlyData.summary.average_monthly_spending)}
                                    </p>
                                    <p>
                                        <strong>Highest Month:</strong> {monthlyData.summary.highest_spending_month}
                                    </p>
                                    <p>
                                        <strong>Lowest Month:</strong> {monthlyData.summary.lowest_spending_month}
                                    </p>
                                    <p>
                                        <strong>Total Annual Spending:</strong> {formatCurrency(monthlyData.summary.total_annual_spending)}
                                    </p>
                                </div>
                            )}

                            {monthlyData.monthly_data && monthlyData.monthly_data.length > 0 ? (
                                <div style={{ overflowX: "auto" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                        <tr>
                                            <th style={{ textAlign: "left", padding: "8px", borderBottom: "2px solid #ddd" }}>Month</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Spending</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Change</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Transactions</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {monthlyData.monthly_data.map((month, index) => (
                                            <tr key={index}>
                                                <td style={{ padding: "8px", borderBottom: "1px solid #ddd" }}>{month.month_name}</td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {formatCurrency(month.total_amount)}
                                                </td>
                                                <td style={{
                                                    textAlign: "right",
                                                    padding: "8px",
                                                    borderBottom: "1px solid #ddd",
                                                    color: month.mom_change > 0 ? "#c62828" : month.mom_change < 0 ? "#2e7d32" : "inherit"
                                                }}>
                                                    {month.mom_change > 0 ? "+" : ""}{month.mom_change}%
                                                </td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {month.transaction_count}
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p>No monthly data available.</p>
                            )}
                        </>
                    )}
                </div>

                {/* Top Merchants Section */}
                <div style={{
                    flex: "1 1 400px",
                    backgroundColor: "white",
                    borderRadius: "8px",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    padding: "20px"
                }}>
                    <h3>Top Merchants</h3>

                    {loading.merchants && (
                        <div>Loading merchant data...</div>
                    )}

                    {error.merchants && (
                        <div style={{ color: "red" }}>{error.merchants}</div>
                    )}

                    {merchantData && !loading.merchants && (
                        <>
                            {merchantData.top_merchants && merchantData.top_merchants.length > 0 ? (
                                <div style={{ overflowX: "auto" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                        <tr>
                                            <th style={{ textAlign: "left", padding: "8px", borderBottom: "2px solid #ddd" }}>Merchant</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Total</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Avg. Amount</th>
                                            <th style={{ textAlign: "right", padding: "8px", borderBottom: "2px solid #ddd" }}>Count</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {merchantData.top_merchants.map((merchant, index) => (
                                            <tr key={index}>
                                                <td style={{ padding: "8px", borderBottom: "1px solid #ddd" }}>{merchant.merchant_name}</td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {formatCurrency(merchant.total_amount)}
                                                </td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {formatCurrency(merchant.average_transaction)}
                                                </td>
                                                <td style={{ textAlign: "right", padding: "8px", borderBottom: "1px solid #ddd" }}>
                                                    {merchant.transaction_count}
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p>No merchant data available.</p>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AnalysisDashboard;