import React, { useState, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";
import axios from "axios";

const PlaidConnect = ({ setAccessToken }) => {
    const [linkToken, setLinkToken] = useState(null);

    useEffect(() => {
        async function fetchLinkToken() {
            const response = await axios.post("https://localhost:8000/link/token/create");
            console.log(response)
            setLinkToken(response.data.link_token);
        }
        fetchLinkToken();
    }, []);

    const { open, ready } = usePlaidLink({
        token: linkToken,
        onSuccess: async (public_token, metadata) => {
            console.log("✅ Public Token:", public_token);

            // Exchange public_token for access_token
            const response = await axios.post("https://localhost:8000/item/public_token/exchange", {
                public_token,
            });

            console.log("✅ Access Token:", response.data.access_token);
            setAccessToken(response.data.access_token);
        },
        onExit: (err, metadata) => {
            if (err) console.error("❌ Error:", err);
        },
    });

    return (
        <div>
            <h2>Connect Your Bank</h2>
            {/*<button onClick={() => open()} disabled={!ready}>*/}
            {/*    Connect Bank*/}
            {/*</button>*/}
        </div>
    );
};

export default PlaidConnect;
