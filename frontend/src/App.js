import React, { useState } from "react";
import PlaidConnect from "./components/PlaidConnect";
import Transactions from "./components/Transactions";
import FileUpload from "./components/FileUpload";
import AnalysisDashboard from "./components/AnalysisDashboard";
import './App.css';

function App() {
    const [accessToken, setAccessToken] = useState(null);
    const [activeTab, setActiveTab] = useState("connect");

    const handleUploadSuccess = () => {
        // Auto-switch to analysis tab after successful upload
        setActiveTab("analysis");
    };

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
                        cursor: "pointer",
                        opacity: accessToken ? 1 : 0.5
                    }}
                    disabled={!accessToken}
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
                        <PlaidConnect setAccessToken={setAccessToken} />
                    </div>
                )}

                {activeTab === "upload" && (
                    <div>
                        <FileUpload onUploadSuccess={handleUploadSuccess} />
                    </div>
                )}

                {activeTab === "transactions" && (
                    <div>
                        {accessToken ? (
                            <Transactions accessToken={accessToken} />
                        ) : (
                            <div style={{ textAlign: "center", padding: "50px" }}>
                                <h2>Bank Connection Required</h2>
                                <p>Please connect your bank account first to view transactions.</p>
                                <button
                                    onClick={() => setActiveTab("connect")}
                                    style={{
                                        padding: "10px 15px",
                                        backgroundColor: "#2196F3",
                                        color: "white",
                                        border: "none",
                                        borderRadius: "4px",
                                        cursor: "pointer",
                                        marginTop: "15px"
                                    }}
                                >
                                    Go to Bank Connection
                                </button>
                            </div>
                        )}
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
