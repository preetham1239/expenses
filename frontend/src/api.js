import axios from "axios";
import https from 'https';

const agent = new https.Agent({
    rejectUnauthorized: false,
    requestCert: false,
    agent: false
});

const api = axios.create({
    baseURL: "https://localhost:8000",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    withCredentials: true,
    httpsAgent: agent,
});

// Add detailed error logging
api.interceptors.request.use(request => {
    console.log('Starting Request:', request)
    return request
});

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response) {
            // The request was made and the server responded with a status code
            console.log('Error Response Data:', error.response.data);
            console.log('Error Response Status:', error.response.status);
            console.log('Error Response Headers:', error.response.headers);
        } else if (error.request) {
            // The request was made but no response was received
            console.log('Error Request:', error.request);
        } else {
            // Something happened in setting up the request
            console.log('Error Message:', error.message);
        }
        console.log('Error Config:', error.config);
        return Promise.reject(error);
    }
);

export default api;
