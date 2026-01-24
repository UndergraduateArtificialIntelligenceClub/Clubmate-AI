import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Terminal, Clock, Cpu, AlertTriangle } from 'lucide-react';

export default function DebugPanel({ debugData }) {
    const [expandedSections, setExpandedSections] = useState({
        request: true,
        processing: true,
    });

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    return (
        <div className="debug-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Header */}
            <div className="debug-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a6e3a1' }}>
                    <Terminal size={16} />
                    <span style={{ fontWeight: 600 }}>Debug Console</span>
                </div>
            </div>

            {/* Content */}
            <div className="debug-content" style={{ flex: 1, overflow: 'auto' }}>
                {!debugData ? (
                    <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '40px 20px' }}>
                        <Terminal size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                        <p style={{ margin: 0 }}>Send a message to see debug information</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {/* Request Section */}
                        <div>
                            <div
                                onClick={() => toggleSection('request')}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    cursor: 'pointer',
                                    marginBottom: '8px',
                                    color: '#89b4fa'
                                }}
                            >
                                <span style={{ fontWeight: 600 }}>Request</span>
                                {expandedSections.request ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </div>
                            {expandedSections.request && debugData.request && (
                                <pre className="debug-json" style={{ margin: 0 }}>
                                    {JSON.stringify(debugData.request, null, 2)}
                                </pre>
                            )}
                        </div>

                        {/* Processing Section */}
                        <div>
                            <div
                                onClick={() => toggleSection('processing')}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    cursor: 'pointer',
                                    marginBottom: '8px',
                                    color: '#f9e2af'
                                }}
                            >
                                <span style={{ fontWeight: 600 }}>Processing</span>
                                {expandedSections.processing ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </div>
                            {expandedSections.processing && debugData.processing && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Cpu size={14} style={{ color: '#a6e3a1' }} />
                                        <span style={{ color: '#cdd6f4' }}>Model: </span>
                                        <span style={{ color: '#a6e3a1' }}>{debugData.processing.model}</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Clock size={14} style={{ color: '#f9e2af' }} />
                                        <span style={{ color: '#cdd6f4' }}>Tokens: </span>
                                        <span style={{ color: '#f9e2af' }}>{debugData.processing.tokens}</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Errors/Warnings */}
                        {debugData.error && (
                            <div>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    marginBottom: '8px',
                                    color: '#f38ba8'
                                }}>
                                    <AlertTriangle size={14} />
                                    <span style={{ fontWeight: 600 }}>Error</span>
                                </div>
                                <pre className="debug-error" style={{ margin: 0 }}>
                                    {debugData.error}
                                </pre>
                            </div>
                        )}

                        {debugData.warning && (
                            <div>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    marginBottom: '8px',
                                    color: '#f9e2af'
                                }}>
                                    <AlertTriangle size={14} />
                                    <span style={{ fontWeight: 600 }}>Warning</span>
                                </div>
                                <pre className="debug-warning" style={{ margin: 0 }}>
                                    {debugData.warning}
                                </pre>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div style={{
                padding: '12px 16px',
                borderTop: '1px solid rgba(255,255,255,0.1)',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                <span>Test Environment</span>
                <span>{new Date().toLocaleTimeString()}</span>
            </div>
        </div>
    );
}
