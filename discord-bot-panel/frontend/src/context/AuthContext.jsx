import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing token and fetch user
    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('token');
            if (!token) {
                setIsLoading(false);
                return;
            }

            try {
                // Set default header
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

                const response = await axios.get('http://localhost:8000/api/auth/me');
                setUser(response.data);
            } catch (error) {
                console.error('Auth check failed', error);
                localStorage.removeItem('token');
                delete axios.defaults.headers.common['Authorization'];
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, []);

    const handleLoginSuccess = (token, userData) => {
        localStorage.setItem('token', token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        if (userData) {
            setUser(userData);
        } else {
            // Fetch user if not provided
            axios.get('http://localhost:8000/api/auth/me')
                .then(res => setUser(res.data))
                .catch(() => logout());
        }
        setIsLoading(false);
    };

    const login = async () => {
        try {
            setIsLoading(true);
            const { data } = await axios.get('http://localhost:8000/api/auth/discord/login?user_redirect=true');
            const { url, state } = data;

            // Open in system browser
            if (window.pywebview) {
                window.pywebview.api.open_external(url);
            } else {
                window.open(url, '_blank');
            }

            // Poll for completion
            const pollInterval = setInterval(async () => {
                try {
                    const pollRes = await axios.get(`http://localhost:8000/api/auth/discord/poll?state=${state}`);
                    if (pollRes.data.status === 'complete') {
                        clearInterval(pollInterval);
                        handleLoginSuccess(pollRes.data.token);
                    }
                } catch (err) {
                    console.error("Polling error", err);
                    // Don't clear interval immediately on network error, but maybe on 400/404
                    if (err.response && err.response.status >= 400) {
                        clearInterval(pollInterval);
                        setIsLoading(false);
                    }
                }
            }, 2000);

            // Timeout after 2 minutes
            setTimeout(() => {
                clearInterval(pollInterval);
                if (!user) setIsLoading(false);
            }, 120000);

        } catch (error) {
            console.error("Login init failed", error);
            setIsLoading(false);
        }
    };

    const loginAsOwner = async () => {
        try {
            setIsLoading(true);
            const { data } = await axios.post('http://localhost:8000/api/auth/dev-login');
            handleLoginSuccess(data.access_token, data.user);
        } catch (error) {
            console.error("Owner login failed", error);
            setIsLoading(false);
            if (error.response?.data?.detail) {
                alert(error.response.data.detail);
            }
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{
            user,
            isLoading,
            login,
            loginAsOwner,
            logout,
            handleLoginSuccess,
            isAuthenticated: !!user
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
