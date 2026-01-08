import React, { useState, useEffect } from 'react';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../../services/api';

const GoogleAuth = () => {
  const [status, setStatus] = useState('disconnected');
  const [loading, setLoading] = useState(true);

  const checkStatus = async () => {
    try {
      const res = await api.getGoogleStatus();
      setStatus(res.data.is_connected ? 'connected' : 'disconnected');
    } catch (err) {
      console.error("Failed to check Google status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const handleConnect = () => {
    api.connectGoogle();
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <NeomorphicCard title="Google Connection">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
          <div className="neu-inset" style={{ padding: '20px', borderRadius: '50%' }}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text-main)' }}>G</span>
          </div>
          <div>
            <h4 style={{ margin: '0 0 4px 0' }}>Gmail & Drive Access</h4>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
              Allows the bot to save attachments and send emails.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={handleConnect} className="neu-outset neu-btn">
            {status === 'connected' ? 'Reconnect Account' : 'Connect Google Account'}
          </button>

          {loading ? (
            <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Checking...</span>
          ) : status === 'connected' ? (
            <span style={{ color: '#00e676', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={16} /> Active
            </span>
          ) : (
            <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertCircle size={16} /> Not Connected
            </span>
          )}
        </div>
      </NeomorphicCard>
    </div>
  );
};

export default GoogleAuth;
