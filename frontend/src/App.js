import React, { useState } from "react";
import PlaidConnect from "./components/PlaidConnect";
import Transactions from "./components/Transactions";

function App() {
    const [accessToken, setAccessToken] = useState(null);

    return (
        <div className="App">
            <h1>Bank Connection</h1>
            <PlaidConnect setAccessToken={setAccessToken} />
            {accessToken && <Transactions accessToken={accessToken} />}
        </div>
    );
}

export default App;