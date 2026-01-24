import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings, Save, AlertCircle } from 'lucide-react';
import api from '../../services/api';
import { Button } from '../../components/global/Button';
import { useToast } from '../../components/global/ToastContext';

const Setup = () => {
    const navigate = useNavigate();
    const { addToast } = useToast();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        discord_client_id: '',
        discord_client_secret: '',
        google_client_id: '',
        google_client_secret: ''
    });

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            await api.saveSetupConfig(formData);
            addToast("Configuration saved successfully!", "success");

            // Delay to allow toast to be seen and config to reload
            setTimeout(() => {
                navigate('/login');
            }, 1500);
        } catch (error) {
            console.error(error);
            addToast("Failed to save configuration. Check console.", "error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
            <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 p-8 rounded-2xl w-full max-w-2xl shadow-2xl">
                <div className="flex items-center gap-4 mb-8">
                    <div className="bg-indigo-500/20 p-3 rounded-xl">
                        <Settings className="w-8 h-8 text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">App Configuration</h1>
                        <p className="text-slate-400">Please configure your OAuth credentials to continue.</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-700">
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-[#5865F2]"></span>
                            Discord Configuration
                        </h2>
                        <div className="grid gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Client ID
                                </label>
                                <input
                                    type="text"
                                    name="discord_client_id"
                                    value={formData.discord_client_id}
                                    onChange={handleChange}
                                    required
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Enter Discord Client ID"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Client Secret
                                </label>
                                <input
                                    type="password"
                                    name="discord_client_secret"
                                    value={formData.discord_client_secret}
                                    onChange={handleChange}
                                    required
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Enter Discord Client Secret"
                                />
                            </div>
                            <div className="text-xs text-slate-500 mt-2">
                                <p>Redirect URI: <code className="bg-slate-800 px-1 py-0.5 rounded text-slate-400">http://localhost:8000/api/auth/discord/callback</code></p>
                                <a href="https://discord.com/developers/applications" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 mt-1 inline-block">
                                    Get keys from Discord Developer Portal
                                </a>
                            </div>
                        </div>
                    </div>

                    <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-700">
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                            Google Configuration
                        </h2>
                        <div className="grid gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Client ID
                                </label>
                                <input
                                    type="text"
                                    name="google_client_id"
                                    value={formData.google_client_id}
                                    onChange={handleChange}
                                    required
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Enter Google Client ID"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">
                                    Client Secret
                                </label>
                                <input
                                    type="password"
                                    name="google_client_secret"
                                    value={formData.google_client_secret}
                                    onChange={handleChange}
                                    required
                                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Enter Google Client Secret"
                                />
                            </div>
                            <div className="text-xs text-slate-500 mt-2">
                                <p>Redirect URI: <code className="bg-slate-800 px-1 py-0.5 rounded text-slate-400">http://localhost:8000/api/auth/google/callback</code></p>
                                <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 mt-1 inline-block">
                                    Get keys from Google Cloud Console
                                </a>
                            </div>
                        </div>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full py-4 text-lg">
                        {loading ? 'Saving...' : 'Save Configuration'}
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default Setup;
