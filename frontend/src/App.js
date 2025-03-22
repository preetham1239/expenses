import React, { useState, useEffect } from "react";
import PlaidConnect from "./components/PlaidConnect";
import Transactions from "./components/Transactions";
import FileUpload from "./components/FileUpload";
import AnalysisDashboard from "./components/AnalysisDashboard";
import axios from "axios";
import './App.css';

function App() {
    const [accessToken, setAccessToken] = useState(null);
    const [activeTab, setActiveTab] = useState("connect");
    const [initialized, setInitialized] = useState(false);
    const [hasValidToken, setHasValidToken] = useState(false);

    // Check for existing token when app loads
    useEffect(() => {
        const checkExistingToken = async () => {
            try {
                // Call new endpoint to check if a valid token exists
                const response = await axios.get("https://localhost:8000/validate-token", {
                    withCredentials: true
                });

                if (response.data.valid) {
                    // If we have a valid token, set the state
                    setHasValidToken(true);
                    // Optionally set the active tab to Transactions directly
                    setActiveTab("transactions");
                }
            } catch (err) {
                console.log("No existing token found or token is invalid");
            } finally {
                setInitialized(true);
            }
        };

        checkExistingToken();
    }, []);

    const handleUploadSuccess = () => {
        // Auto-switch to analysis tab after successful upload
        setActiveTab("analysis");
    };

    // Watch for accessToken changes and navigate to transactions tab when it's set
    useEffect(() => {
        if (accessToken) {
            // When accessToken is set, automatically switch to transactions tab
            setActiveTab("transactions");
        }
    }, [accessToken]);

    // Show loading until initialization completes
    if (!initialized) {
        return (
            <div className="App" style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
                <div style={{ textAlign: "center" }}>
                    <p>Loading application...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            <header className="App-header" style={{
                backgroundColor: "#282c34",
                padding: "20px 0",
                minHeight: "auto"
            }}>
                <h1 style={{ margin: 0, color: "white" }}>Expense Tracker</h1>
            </header>

            <nav style={{
                display: "flex",
                justifyContent: "center",
                backgroundColor: "#f5f5f5",
                padding: "10px 0",
                borderBottom: "1px solid #e0e0e0"
            }}>
                <button
                    onClick={() => setActiveTab("connect")}
                    style={{
                        padding: "8px 15px",
                        margin: "0 5px",
                        backgroundColor: activeTab === "connect" ? "#2196F3" : "#f8f8f8",
                        color: activeTab === "connect" ? "white" : "black",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Connect Bank
                </button>

                <button
                    onClick={() => setActiveTab("upload")}
                    style={{
                        padding: "8px 15px",
                        margin: "0 5px",
                        backgroundColor: activeTab === "upload" ? "#2196F3" : "#f8f8f8",
                        color: activeTab === "upload" ? "white" : "black",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Upload Data
                </button>

                <button
                    onClick={() => setActiveTab("transactions")}
                    style={{
                        padding: "8px 15px",
                        margin: "0 5px",
                        backgroundColor: activeTab === "transactions" ? "#2196F3" : "#f8f8f8",
                        color: activeTab === "transactions" ? "white" : "black",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Transactions
                </button>

                <button
                    onClick={() => setActiveTab("analysis")}
                    style={{
                        padding: "8px 15px",
                        margin: "0 5px",
                        backgroundColor: activeTab === "analysis" ? "#2196F3" : "#f8f8f8",
                        color: activeTab === "analysis" ? "white" : "black",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        cursor: "pointer"
                    }}
                >
                    Analysis
                </button>
            </nav>

            <main style={{ padding: "20px" }}>
                {activeTab === "connect" && (
                    <div>
                        <PlaidConnect setAccessToken={setAccessToken} hasValidToken={hasValidToken} />
                    </div>
                )}

                {activeTab === "upload" && (
                    <div>
                        <FileUpload onUploadSuccess={handleUploadSuccess} />
                    </div>
                )}

                {activeTab === "transactions" && (
                    <div>
                        <Transactions accessToken={accessToken} />
                    </div>
                )}

                {activeTab === "analysis" && (
                    <div>
                        <AnalysisDashboard />
                    </div>
                )}
            </main>

            <footer style={{
                marginTop: "30px",
                padding: "15px",
                backgroundColor: "#f5f5f5",
                borderTop: "1px solid #e0e0e0",
                textAlign: "center",
                fontSize: "14px",
                color: "#666"
            }}>
                <p>Expense Tracker &copy; 2025 - Your Personal Finance Assistant</p>
            </footer>
        </div>
    );
}

export default App;
