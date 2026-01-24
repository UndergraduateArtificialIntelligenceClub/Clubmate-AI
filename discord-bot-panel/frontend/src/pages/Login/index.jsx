import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Bot, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const Login = () => {
  const { login } = useAuth();
  const searchParams = new URLSearchParams(window.location.search);
  const error = searchParams.get('error');
  const navigate = useNavigate();

  // Check if configured
  useEffect(() => {
    const checkConfig = async () => {
      try {
        const res = await api.getSetupStatus();
        if (!res.data.is_configured) {
          navigate('/setup');
        }
      } catch (err) {
        console.error("Failed to check config", err);
      }
    };
    checkConfig();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 p-8 rounded-2xl w-full max-w-md shadow-2xl relative z-10">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-500 p-3 rounded-xl shadow-lg shadow-indigo-500/20">
              <Bot className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-slate-400">Sign in to manage your Discord bot</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg mb-6 text-sm text-center">
            Authentication failed. Please try again.
          </div>
        )}

        <button
          onClick={login}
          className="w-full bg-[#5865F2] hover:bg-[#4752C4] text-white py-3 px-4 rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-2 group shadow-lg shadow-[#5865F2]/20 hover:shadow-[#5865F2]/40 hover:-translate-y-0.5"
        >
          <Zap className="w-5 h-5 group-hover:scale-110 transition-transform" />
          Login with Discord
        </button>

        <p className="text-slate-500 text-xs text-center mt-6">
          By logging in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
};

export default Login;
