import React, { useState, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";
import axios from "axios";

const PlaidConnect = ({ setAccessToken }) => {
    const [linkToken, setLinkToken] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [retryCount, setRetryCount] = useState(0); // Prevent infinite retries

    useEffect(() => {
        // Only fetch a new token if we don't have one yet or if explicitly retrying
        // but limit to max 3 retries
        if ((!linkToken || retryCount > 0) && retryCount < 3) {
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
        }
    }, [linkToken, retryCount]);

    const onSuccess = async (public_token, metadata) => {
        console.log("✅ Plaid Link Success - Public Token:", public_token);
        console.log("✅ Metadata:", metadata);

        try {
            const response = await axios.post("https://localhost:8000/item/public_token/exchange", {
                public_token,
            }, {
                headers: {
                    "Content-Type": "application/json"
                },
                withCredentials: true
            });

            console.log("✅ Access Token Response:", response.data);

            if (response.data.access_token) {
                setAccessToken(response.data.access_token);
            } else {
                setError("Could not retrieve access token.");
            }
        } catch (err) {
            console.error("❌ Error exchanging token:", err);
            setError("Failed to connect to your bank. Please try again.");
        }
    };

    const onExit = (err, metadata) => {
        if (err) {
            console.error("❌ Plaid Link Error:", err);

            // Handle specific OAuth errors without causing infinite retry loops
            if (err.error_code === "INVALID_FIELD" &&
                err.error_message &&
                err.error_message.includes("oauth")) {
                setError("OAuth configuration error: " + err.error_message);
                // Only retry once
                if (retryCount < 1) {
                    console.log("Will retry once with a new token");
                    setRetryCount(prev => prev + 1);
                    setLinkToken(null);
                }
            } else {
                setError(err.display_message || err.error_message || "An error occurred.");
            }
        }

        console.log("Link closed:", metadata);
    };

    // Simple configuration without OAuth for now
    const config = {
        token: linkToken,
        onSuccess,
        onExit
    };

    const { open, ready } = usePlaidLink(config);

    return (
        <div className="plaid-connect-container" style={{ margin: "20px" }}>
            <h2>Connect Your Bank</h2>

            {error && (
                <div style={{ color: 'red', marginBottom: '15px' }}>
                    {error}
                </div>
            )}

            <button
                onClick={() => {
                    if (ready && linkToken) {
                        open();
                    }
                }}
                disabled={!ready || isLoading || !linkToken}
                style={{
                    padding: '10px 15px',
                    backgroundColor: (ready && linkToken) ? '#4CAF50' : '#cccccc',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (ready && linkToken) ? 'pointer' : 'not-allowed',
                }}
            >
                {isLoading ? "Loading..." : "Connect Bank Account"}
            </button>

            {retryCount >= 3 && (
                <p style={{ color: 'red', marginTop: '10px' }}>
                    Multiple attempts failed. Please reload the page and try again.
                </p>
            )}
        </div>
    );
};

export default PlaidConnect;