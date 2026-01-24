import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { CheckCircle, AlertCircle, RefreshCw, User, LogOut } from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const Accounts = () => {
    const { user, logout } = useAuth();
    const [googleStatus, setGoogleStatus] = useState('disconnected');
    const [googleEmail, setGoogleEmail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchParams] = useSearchParams();

    const checkGoogleStatus = async () => {
        try {
            const res = await api.getGoogleStatus();
            setGoogleStatus(res.data.is_connected ? 'connected' : 'disconnected');
            setGoogleEmail(res.data.email || null);
        } catch (err) {
            console.error("Failed to check Google status", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Check if we just came back from Google OAuth
        const urlStatus = searchParams.get('status');
        if (urlStatus === 'success') {
            const interval = setInterval(checkGoogleStatus, 1000);
            setTimeout(() => clearInterval(interval), 5000);
        }
        checkGoogleStatus();
    }, [searchParams]);

    const handleConnectGoogle = async () => {
        await api.connectGoogle();
        const interval = setInterval(checkGoogleStatus, 2000);
        setTimeout(() => clearInterval(interval), 30000);
    };

    const handleDisconnectGoogle = async () => {
        try {
            await api.disconnectGoogle();
            setGoogleStatus('disconnected');
            setGoogleEmail(null);
        } catch (err) {
            console.error("Failed to disconnect Google", err);
        }
    };

    return (
        <div style={{ display: 'grid', gap: '32px' }}>
            {/* Discord Account Section */}
            <NeomorphicCard title="Discord Account">
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '16px' }}>
                    <div className="neu-outset" style={{ padding: '4px', borderRadius: '50%' }}>
                        {user?.avatar ? (
                            <img
                                src={`https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`}
                                alt="Avatar"
                                style={{ width: '80px', height: '80px', borderRadius: '50%' }}
                            />
                        ) : (
                            <div className="neu-inset" style={{ width: '80px', height: '80px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <User size={40} color="var(--text-secondary)" />
                            </div>
                        )}
                    </div>
                    <div style={{ flex: 1 }}>
                        <h3 style={{ margin: '0 0 4px 0', fontSize: '20px' }}>{user?.username || 'Unknown User'}</h3>
                        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
                            Discord ID: <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: '4px' }}>{user?.id || 'N/A'}</code>
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
                            <span style={{
                                background: 'rgba(88, 101, 242, 0.2)',
                                color: '#5865F2',
                                padding: '4px 12px',
                                borderRadius: '20px',
                                fontSize: '12px',
                                fontWeight: 'bold',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                            }}>
                                <CheckCircle size={14} /> Authenticated via Discord
                            </span>
                        </div>
                    </div>
                    <button onClick={logout} className="neu-outset neu-btn" style={{ color: 'var(--danger)', gap: '8px' }}>
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </NeomorphicCard>

            {/* Google Connection Section */}
            <NeomorphicCard title="External Connections">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                    <div className="neu-inset" style={{ padding: '20px', borderRadius: '50%', background: '#fff' }}>
                        <img
                            src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg"
                            alt="Google"
                            style={{ width: '24px', height: '24px' }}
                        />
                    </div>
                    <div style={{ flex: 1 }}>
                        <h4 style={{ margin: '0 0 4px 0' }}>Google Services</h4>
                        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
                            Connect your Google account to enable Gmail and Drive features for the bot.
                        </p>
                        {googleEmail && (
                            <p style={{ margin: '8px 0 0 0', color: 'var(--accent)', fontSize: '13px', fontWeight: 500 }}>
                                Linked to: {googleEmail}
                            </p>
                        )}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        {loading ? (
                            <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                                <RefreshCw size={14} className="animate-spin" />
                            </span>
                        ) : googleStatus === 'connected' ? (
                            <Badge variant="success">Connected</Badge>
                        ) : (
                            <Badge variant="neutral">Not Linked</Badge>
                        )}
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button onClick={handleConnectGoogle} className="neu-outset neu-btn" style={{ flex: 1 }}>
                        {googleStatus === 'connected' ? 'Change Google Account' : 'Connect Google Account'}
                    </button>

                    {googleStatus === 'connected' && (
                        <button onClick={handleDisconnectGoogle} className="neu-outset neu-btn" style={{ color: 'var(--danger)' }}>
                            Disconnect
                        </button>
                    )}
                </div>
            </NeomorphicCard>
        </div>
    );
};

// Helper Badge component since we have it in theme but maybe not as a standalone here
const Badge = ({ children, variant }) => {
    const styles = {
        success: { background: 'rgba(0, 230, 118, 0.2)', color: '#00e676' },
        neutral: { background: 'rgba(141, 151, 165, 0.2)', color: 'var(--text-secondary)' }
    };
    const style = styles[variant] || styles.neutral;

    return (
        <span style={{
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            ...style
        }}>
            {children}
        </span>
    );
};

export default Accounts;
