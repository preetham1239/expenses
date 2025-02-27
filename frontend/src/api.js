import axios from "axios";

// Base API client configuration
const api = axios.create({
    baseURL: "https://localhost:8000",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    withCredentials: true,
    // For development only - disables certificate validation
    // This is handled differently in the browser vs Node.js
    validateStatus: () => true,
    timeout: 10000, // 10 second timeout
});

// Request interceptor for logging and adding additional headers
api.interceptors.request.use(
    request => {
        console.log('Starting Request:', {
            url: request.url,
            method: request.method,
            headers: request.headers,
        });
        return request;
    },
    error => {
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for detailed error logging
api.interceptors.response.use(
    response => {
        console.log('Response received:', {
            status: response.status,
            statusText: response.statusText,
            url: response.config.url
        });
        return response;
    },
    error => {
        if (error.response) {
            // The server responded with a status code outside the 2xx range
            console.error('Error Response:', {
                status: error.response.status,
                statusText: error.response.statusText,
                data: error.response.data,
                headers: error.response.headers,
            });
        } else if (error.request) {
            // The request was made but no response was received
            console.error('No Response Received:', {
                config: error.config,
            });
        } else {
            // Something happened in setting up the request
            console.error('Request Setup Error:', error.message);
        }

        // Add user-friendly error messages
        const errorMessage = getErrorMessage(error);
        error.userMessage = errorMessage;

        return Promise.reject(error);
    }
);

// Function to generate user-friendly error messages
function getErrorMessage(error) {
    if (error.response) {
        // Server responded with error
        const status = error.response.status;

        if (status === 401) {
            return "Authentication error. Please try logging in again.";
        } else if (status === 403) {
            return "You don't have permission to access this resource.";
        } else if (status === 404) {
            return "The requested resource was not found.";
        } else if (status === 500) {
            return "A server error occurred. Please try again later.";
        } else {
            return error.response.data.error || "An unexpected error occurred.";
        }
    } else if (error.request) {
        // Network error
        return "Unable to connect to the server. Please check your internet connection.";
    } else {
        // Other errors
        return "An unexpected error occurred. Please try again.";
    }
}

export default api;