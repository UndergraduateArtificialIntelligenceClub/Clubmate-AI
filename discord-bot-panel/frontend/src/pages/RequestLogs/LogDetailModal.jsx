import React from 'react';
import {
    X, Clock, Server, Hash, User, Terminal,
    Zap, CheckCircle, XCircle, AlertTriangle, Copy
} from 'lucide-react';
import { Badge } from '../../components/global/Badge';
import { Button } from '../../components/global/Button';
import { useToast } from '../../components/global/ToastContext';

const InfoRow = ({ icon: Icon, label, value, copyable }) => {
    const { addToast } = useToast();

    const handleCopy = () => {
        navigator.clipboard.writeText(value);
        addToast('Copied to clipboard', 'success');
    };

    return (
        <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            padding: '12px 0',
            borderBottom: '1px solid var(--glass-border)'
        }}>
            <Icon size={16} style={{ color: 'var(--text-secondary)', marginTop: '2px', flexShrink: 0 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    {label}
                </div>
                <div style={{
                    fontSize: '14px',
                    wordBreak: 'break-word',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    {value}
                    {copyable && (
                        <button
                            onClick={handleCopy}
                            style={{
                                background: 'none',
                                border: 'none',
                                padding: '4px',
                                cursor: 'pointer',
                                color: 'var(--text-secondary)',
                                opacity: 0.6
                            }}
                        >
                            <Copy size={12} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default function LogDetailModal({ log, onClose }) {
    const { addToast } = useToast();

    if (!log) return null;

    const formatTimestamp = (ts) => {
        const date = new Date(ts);
        return date.toLocaleString();
    };

    const getStatusIcon = () => {
        switch (log.status) {
            case 'success': return <CheckCircle size={18} style={{ color: 'var(--status-online)' }} />;
            case 'error': return <XCircle size={18} style={{ color: 'var(--discord-red)' }} />;
            case 'timeout': return <AlertTriangle size={18} style={{ color: 'var(--status-idle)' }} />;
            default: return null;
        }
    };

    const getStatusBadgeVariant = () => {
        switch (log.status) {
            case 'success': return 'success';
            case 'error': return 'error';
            case 'timeout': return 'warning';
            default: return 'neutral';
        }
    };

    return (
        <>
            {/* Backdrop */}
            <div
                onClick={onClose}
                style={{
                    position: 'fixed',
                    inset: 0,
                    background: 'rgba(0, 0, 0, 0.6)',
                    zIndex: 1000,
                    animation: 'fadeIn 150ms ease'
                }}
            />

            {/* Modal */}
            <div
                className="animate-slideUp"
                style={{
                    position: 'fixed',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '90%',
                    maxWidth: '600px',
                    maxHeight: '85vh',
                    overflow: 'auto',
                    background: 'var(--bg-color)',
                    borderRadius: '20px',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                    zIndex: 1001,
                }}
            >
                {/* Header */}
                <div style={{
                    padding: '20px 24px',
                    borderBottom: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    position: 'sticky',
                    top: 0,
                    background: 'var(--bg-color)',
                    zIndex: 1
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {getStatusIcon()}
                        <div>
                            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Request Details</h3>
                            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                ID: {log.id}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'var(--glass-bg)',
                            border: 'none',
                            borderRadius: '8px',
                            padding: '8px',
                            cursor: 'pointer',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Content */}
                <div style={{ padding: '0 24px 24px' }}>
                    {/* Status Banner */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '16px',
                        margin: '20px 0',
                        background: 'var(--glass-bg)',
                        borderRadius: '12px'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Badge variant={getStatusBadgeVariant()}>{log.status}</Badge>
                            <span style={{ fontSize: '14px', color: 'var(--text-main)' }}>
                                {log.status === 'success' && 'Request completed successfully'}
                                {log.status === 'error' && 'Request failed with an error'}
                                {log.status === 'timeout' && 'Request timed out'}
                            </span>
                        </div>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            color: log.executionTime > 1000 ? 'var(--status-idle)' : 'var(--text-secondary)',
                            fontFamily: 'monospace'
                        }}>
                            <Clock size={14} />
                            {log.executionTime}ms
                        </div>
                    </div>

                    {/* Request Info */}
                    <InfoRow
                        icon={Clock}
                        label="Timestamp"
                        value={formatTimestamp(log.timestamp)}
                    />
                    <InfoRow
                        icon={Server}
                        label="Server"
                        value={`${log.serverName} (${log.serverId})`}
                        copyable
                    />
                    <InfoRow
                        icon={Hash}
                        label="Channel"
                        value={`#${log.channelName}`}
                    />
                    <InfoRow
                        icon={User}
                        label="User"
                        value={`${log.userName} (${log.userId})`}
                        copyable
                    />
                    <InfoRow
                        icon={Terminal}
                        label="Command"
                        value={
                            <code style={{
                                background: 'var(--glass-bg)',
                                padding: '4px 8px',
                                borderRadius: '6px',
                                fontSize: '13px'
                            }}>
                                {log.command}
                            </code>
                        }
                    />
                    <InfoRow
                        icon={Zap}
                        label="Feature Triggered"
                        value={log.featureTriggered}
                    />

                    {/* Full Prompt */}
                    <div style={{ marginTop: '20px' }}>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                            Full Message / Prompt
                        </div>
                        <div
                            className="neu-inset"
                            style={{
                                padding: '16px',
                                borderRadius: '12px',
                                fontFamily: "'JetBrains Mono', monospace",
                                fontSize: '13px',
                                lineHeight: 1.6,
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word'
                            }}
                        >
                            {log.prompt}
                        </div>
                    </div>

                    {/* Response/Error */}
                    {(log.response || log.error) && (
                        <div style={{ marginTop: '20px' }}>
                            <div style={{
                                fontSize: '12px',
                                color: log.error ? 'var(--discord-red)' : 'var(--text-secondary)',
                                marginBottom: '8px'
                            }}>
                                {log.error ? 'Error' : 'Response'}
                            </div>
                            <div
                                className="debug-panel"
                                style={{
                                    padding: '16px',
                                    borderRadius: '12px',
                                }}
                            >
                                <pre style={{
                                    margin: 0,
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                    color: log.error ? '#f38ba8' : '#a6e3a1'
                                }}>
                                    {log.error || JSON.stringify(log.response, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div style={{
                        display: 'flex',
                        justifyContent: 'flex-end',
                        gap: '12px',
                        marginTop: '24px',
                        paddingTop: '20px',
                        borderTop: '1px solid var(--glass-border)'
                    }}>
                        <Button variant="ghost" onClick={onClose}>Close</Button>
                    </div>
                </div>
            </div>
        </>
    );
}
