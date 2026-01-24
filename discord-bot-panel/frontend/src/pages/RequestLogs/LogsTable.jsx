import React from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';
import { Badge } from '../../components/global/Badge';

const columns = [
    { key: 'timestamp', label: 'Time', width: '120px' },
    { key: 'serverName', label: 'Server' },
    { key: 'channelName', label: 'Channel', width: '120px' },
    { key: 'userName', label: 'User', width: '120px' },
    { key: 'command', label: 'Command', width: '100px' },
    { key: 'invocationType', label: 'Type', width: '90px' },
    { key: 'featureTriggered', label: 'Feature', width: '100px' },
    { key: 'status', label: 'Status', width: '100px' },
    { key: 'executionTime', label: 'Time (ms)', width: '90px' },
];

const StatusBadge = ({ status }) => {
    const variants = {
        success: 'success',
        error: 'error',
        timeout: 'warning',
    };
    return <Badge variant={variants[status] || 'neutral'}>{status}</Badge>;
};

const TypeBadge = ({ type }) => {
    const colors = {
        prefix: 'var(--discord-blurple)',
        mention: 'var(--discord-green)',
        slash: 'var(--discord-fuchsia)',
    };
    return (
        <span style={{
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'uppercase',
            background: `${colors[type]}22`,
            color: colors[type],
        }}>
            {type}
        </span>
    );
};

export default function LogsTable({ logs, sortConfig, onSort, onRowClick }) {
    const formatTime = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();

        if (isToday) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
            date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getSortIcon = (key) => {
        if (sortConfig.key !== key) {
            return <ArrowUpDown size={14} style={{ opacity: 0.3 }} />;
        }
        return sortConfig.direction === 'asc'
            ? <ArrowUp size={14} />
            : <ArrowDown size={14} />;
    };

    if (logs.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
                <p style={{ margin: 0, fontSize: '15px' }}>No request logs found</p>
                <p style={{ margin: '8px 0 0', fontSize: '13px' }}>Logs will appear here when your bot receives requests</p>
            </div>
        );
    }

    return (
        <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
                <thead>
                    <tr>
                        {columns.map(col => (
                            <th
                                key={col.key}
                                onClick={() => onSort(col.key)}
                                style={{ width: col.width }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    {col.label}
                                    {getSortIcon(col.key)}
                                </div>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {logs.map(log => (
                        <tr
                            key={log.id}
                            onClick={() => onRowClick(log)}
                            style={{ cursor: 'pointer' }}
                        >
                            <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                                {formatTime(log.timestamp)}
                            </td>
                            <td>
                                <div>
                                    <div style={{ fontWeight: 500 }}>{log.serverName}</div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                        {log.serverId}
                                    </div>
                                </div>
                            </td>
                            <td style={{ color: 'var(--text-secondary)' }}>#{log.channelName}</td>
                            <td>
                                <div>
                                    <div>{log.userName}</div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                        {log.userId.slice(0, 8)}...
                                    </div>
                                </div>
                            </td>
                            <td>
                                <code style={{
                                    background: 'var(--glass-bg)',
                                    padding: '4px 8px',
                                    borderRadius: '6px',
                                    fontSize: '12px'
                                }}>
                                    {log.command}
                                </code>
                            </td>
                            <td><TypeBadge type={log.invocationType} /></td>
                            <td style={{ fontSize: '13px' }}>{log.featureTriggered}</td>
                            <td><StatusBadge status={log.status} /></td>
                            <td style={{
                                fontFamily: 'monospace',
                                fontSize: '13px',
                                color: log.executionTime > 1000 ? 'var(--status-idle)' : 'var(--text-main)'
                            }}>
                                {log.executionTime}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
