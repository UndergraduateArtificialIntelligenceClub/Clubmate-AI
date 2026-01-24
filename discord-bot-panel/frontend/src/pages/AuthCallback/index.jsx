import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const AuthCallback = () => {
    const navigate = useNavigate();
    const { handleLoginSuccess } = useAuth();

    useEffect(() => {
        const handleCallback = () => {
            // Get token from URL query params
            const searchParams = new URLSearchParams(window.location.search);
            const token = searchParams.get('token');

            if (token) {
                // Update context state
                handleLoginSuccess(token);
                // Redirect to dashboard
                navigate('/', { replace: true });
            } else {
                // No token, redirect to login
                navigate('/login?error=no_token');
            }
        };

        handleCallback();
    }, [navigate, handleLoginSuccess]);

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                <p className="text-slate-400">Authenticating...</p>
            </div>
        </div>
    );
};

export default AuthCallback;
