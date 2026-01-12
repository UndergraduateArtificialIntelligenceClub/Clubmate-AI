import React, { useState, useEffect } from 'react';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { TrendingUp, Users, AlertTriangle, Activity, Trash2, RefreshCcw } from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../components/global/ToastContext';
import { Button } from '../../components/global/Button';

const StatCard = ({ title, value, icon: Icon, trend, color }) => (
  <NeomorphicCard style={{ alignItems: 'flex-start' }}>
    <div className="neu-inset" style={{ padding: '12px', borderRadius: '50%', color: color, marginBottom: '16px' }}>
      <Icon size={24} />
    </div>
    <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{title}</span>
    <h2 style={{ margin: '8px 0', fontSize: '32px' }}>{value}</h2>
    <span style={{ fontSize: '12px', color: '#00e676', display: 'flex', alignItems: 'center', gap: '4px' }}>
      <TrendingUp size={12} /> {trend}
    </span>
  </NeomorphicCard>
);

export default function Dashboard() {
  const [stats, setStats] = useState({ cpu: 0, memory: 0, total_contacts: 0, active_bans: 0 });
  const [logs, setLogs] = useState([]);
  const { addToast } = useToast();

  const loadData = async () => {
    try {
      const statRes = await api.getStats();
      setStats(statRes.data);
      const logRes = await api.getLogs();
      setLogs(logRes.data);
    } catch (e) {
      console.error("Dashboard load failed", e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleClearLogs = async () => {
    if (!window.confirm("Are you sure you want to clear all system logs?")) return;
    try {
      await api.clearLogs();
      setLogs([]);
      addToast("System logs cleared successfully", "success");
    } catch (err) {
      addToast("Failed to clear logs", "error");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
        <StatCard title="Total Contacts" value={stats.total_contacts} icon={Users} trend="Live" color="var(--accent)" />
        <StatCard title="Active Bans" value={stats.active_bans} icon={AlertTriangle} trend="Action required" color="var(--danger)" />
        <StatCard title="System CPU" value={`${stats.cpu}%`} icon={Activity} trend="Real-time" color="#00e676" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <NeomorphicCard
          title="Recent Activity Log"
          actions={
            <Button onClick={handleClearLogs} variant="danger" style={{ padding: '6px 12px', fontSize: '12px' }}>
              <Trash2 size={14} /> Clear History
            </Button>
          }
        >
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: '300px', overflowY: 'auto' }}>
            {logs.length > 0 ? logs.map(log => (
              <li key={log.id} style={{ padding: '16px 0', borderBottom: '1px solid rgba(0,0,0,0.05)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-main)' }}>
                  <b>{log.action}</b>: {
                    typeof log.details === 'object' && log.details !== null
                      ? Object.entries(log.details).map(([k, v]) => `${k}=${v}`).join(', ')
                      : String(log.details || '')
                  }
                </span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                  {new Date(log.created_at).toLocaleTimeString()}
                </span>
              </li>
            )) : <li style={{ padding: '16px 0', color: 'var(--text-secondary)' }}>No recent activity.</li>}
          </ul>
        </NeomorphicCard>

        <NeomorphicCard title="System Health">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span>CPU Usage</span>
                <span>{stats.cpu}%</span>
              </div>
              <div className="neu-inset" style={{ height: '8px', width: '100%', overflow: 'hidden' }}>
                <div style={{ width: `${stats.cpu}%`, height: '100%', background: 'var(--accent)', borderRadius: '8px', transition: 'width 0.5s' }}></div>
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span>Memory</span>
                <span>{stats.memory}%</span>
              </div>
              <div className="neu-inset" style={{ height: '8px', width: '100%', overflow: 'hidden' }}>
                <div style={{ width: `${stats.memory}%`, height: '100%', background: 'var(--danger)', borderRadius: '8px', transition: 'width 0.5s' }}></div>
              </div>
            </div>
          </div>
        </NeomorphicCard>
      </div>
    </div>
  );
}
