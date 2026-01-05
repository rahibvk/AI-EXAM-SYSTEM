import axios from 'axios';

/**
 * Axios instance configured for the API.
 * Base URL is set to localhost:8000/api/v1.
 */
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Request Interceptor
 * Automatically attaches the Bearer token from localStorage to every request.
 */
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

/**
 * Response Interceptor
 * Handles global error responses, specifically 401 Unauthorized.
 * Redirects to login if the token is invalid or expired.
 */
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token invalid or expired
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            // Optional: Redirect to login if not already there
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
