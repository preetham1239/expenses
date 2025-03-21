import React, { useState, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";
import axios from "axios";

const PlaidConnect = ({ setAccessToken }) => {
    const [linkToken, setLinkToken] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // This function will open Plaid Link in a new tab/window
    const openPlaidInNewTab = (token) => {
        const plaidUrl = `https://cdn.plaid.com/link/v2/stable/link.html?isWebview=true&token=${token}`;
        window.open(plaidUrl, '_blank', 'width=600,height=600');

        // We'll need to poll for the access token since we won't get a callback
        alert('After connecting your bank in the new window, please come back to this page and click "Check Connection Status"');
    };

    useEffect(() => {
        const fetchLinkToken = async () => {
            setIsLoading(true);
            try {
                console.log("Fetching link token...");
                const response = await axios.post("https://localhost:8000/link/token/create", {}, {
                    headers: {
                        "Content-Type": "application/json"
                    },
                    withCredentials: true
                });

                console.log("Link token response:", response.data);

                if (response.data.link_token) {
                    setLinkToken(response.data.link_token);
                    setError(null);
                } else {
                    console.error("No link token received:", response.data);
                    setError("Failed to initialize bank connection.");
                }
            } catch (err) {
                console.error("Error fetching link token:", err);
                setError("Failed to connect to server. Please try again.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchLinkToken();
    }, []);

    // For checking connection status after linking in new tab
    const checkConnectionStatus = async () => {
        // In a real app, you'd poll your backend to check if a connection was made
        // For this demo, we'll just show a message
        alert('In a real app, this would check if your bank connection was successful.');
    };

    // Normal Plaid Link config
    const config = {
        token: linkToken,
        onSuccess: async (public_token, metadata) => {
            console.log("✅ Plaid Link Success - Public Token:", public_token);
            try {
                const response = await axios.post("https://localhost:8000/item/public_token/exchange", {
                    public_token,
                }, {
                    headers: {
                        "Content-Type": "application/json"
                    },
                    withCredentials: true
                });

                if (response.data.access_token) {
                    setAccessToken(response.data.access_token);
                }
            } catch (err) {
                console.error("Error exchanging token:", err);
                setError("Failed to connect bank. Try again.");
            }
        },
        onExit: (err, metadata) => {
            if (err) console.error("Plaid Link Error:", err);
        }
    };

    const { open, ready } = usePlaidLink(config);

    return (
        <div className="plaid-connect-container" style={{ margin: "20px" }}>
            <h2>Connect Your Bank</h2>

            {error && (
                <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffeeee', borderRadius: '4px' }}>
                    <p><strong>Error:</strong> {error}</p>
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                {/* Normal Plaid Link Button */}
                <button
                    onClick={() => open()}
                    disabled={!ready || isLoading || !linkToken}
                    style={{
                        padding: '12px 20px',
                        backgroundColor: (ready && linkToken) ? '#4CAF50' : '#cccccc',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: (ready && linkToken) ? 'pointer' : 'not-allowed',
                        fontWeight: 'bold',
                        fontSize: '16px'
                    }}
                >
                    {isLoading ? "Loading..." : "Connect Bank (Normal)"}
                </button>

                {/* External Plaid Link Button */}
                <button
                    onClick={() => linkToken && openPlaidInNewTab(linkToken)}
                    disabled={!linkToken || isLoading}
                    style={{
                        padding: '12px 20px',
                        backgroundColor: linkToken ? '#2196F3' : '#cccccc',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: linkToken ? 'pointer' : 'not-allowed',
                        fontWeight: 'bold',
                        fontSize: '16px'
                    }}
                >
                    Connect Bank in New Window
                </button>

                {/* Status Check Button */}
                <button
                    onClick={checkConnectionStatus}
                    style={{
                        padding: '12px 20px',
                        backgroundColor: '#FFC107',
                        color: 'black',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        fontSize: '16px'
                    }}
                >
                    Check Connection Status
                </button>
            </div>

            <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '4px', fontSize: '14px' }}>
                <h3 style={{ marginTop: 0 }}>Troubleshooting Tips:</h3>
                <ol style={{ marginLeft: '20px', textAlign: 'left' }}>
                    <li>Try the "Connect Bank in New Window" option if the normal flow doesn't work</li>
                    <li>Make sure to allow pop-ups in your browser</li>
                    <li>If using Safari, you may need to enable cross-site tracking</li>
                    <li>Try using Chrome or Firefox if you encounter issues</li>
                </ol>
            </div>
        </div>
    );
};

export default PlaidConnect;
