import React from 'react';
import { useBot } from '../../context/BotContext';
import { Toggle } from '../../components/global/Toggle';
import { Tabs } from '../../components/global/Tabs';

const modeTabs = [
    { id: 'prefix', label: 'Prefix Only' },
    { id: 'mention', label: 'Mention Only' },
    { id: 'hybrid', label: 'Hybrid Mode' },
];

export default function InvocationSettings() {
    const { botConfig, updateInvocation } = useBot();
    const { invocation } = botConfig;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Command Prefix */}
            <div className="form-group">
                <label className="form-label">Command Prefix</label>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    {['!', '/', '?', '.', '>', '::'].map((prefix) => (
                        <button
                            key={prefix}
                            className={`neu-outset`}
                            onClick={() => updateInvocation({ prefix })}
                            style={{
                                padding: '12px 24px',
                                borderRadius: '12px',
                                border: 'none',
                                fontSize: '18px',
                                fontFamily: "'JetBrains Mono', monospace",
                                color: invocation.prefix === prefix ? 'var(--accent)' : 'var(--text-secondary)',
                                cursor: 'pointer',
                                boxShadow: invocation.prefix === prefix
                                    ? 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)'
                                    : '6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light)',
                                transition: 'all 150ms ease',
                            }}
                        >
                            {prefix}
                        </button>
                    ))}
                    <input
                        type="text"
                        className="form-input"
                        value={!['!', '/', '?', '.', '>', '::'].includes(invocation.prefix) ? invocation.prefix : ''}
                        onChange={(e) => updateInvocation({ prefix: e.target.value.slice(0, 3) })}
                        placeholder="Custom"
                        style={{ width: '100px' }}
                    />
                </div>
            </div>

            {/* Mention Toggle */}
            <div className="form-group">
                <label className="form-label">Mention-based Invocation</label>
                <Toggle
                    checked={invocation.mentionEnabled}
                    onChange={(checked) => updateInvocation({ mentionEnabled: checked })}
                    label="Enable @BotName mentions"
                    description={`Users can mention the bot like @${botConfig.identity.username} help`}
                />
            </div>

            {/* Custom Calling Tag */}
            <div className="form-group">
                <label className="form-label">Custom Calling Tag (Optional)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <input
                        type="text"
                        className="form-input"
                        value={invocation.customTag}
                        onChange={(e) => updateInvocation({ customTag: e.target.value })}
                        placeholder="e.g., ::, >>, #bot"
                        style={{ maxWidth: '200px' }}
                    />
                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        Example: <code style={{ background: 'var(--glass-bg)', padding: '4px 8px', borderRadius: '4px' }}>
                            {invocation.customTag || '::'}help
                        </code>
                    </span>
                </div>
            </div>

            {/* Invocation Mode */}
            <div className="form-group">
                <label className="form-label">Invocation Mode</label>
                <Tabs
                    tabs={modeTabs}
                    activeTab={invocation.mode}
                    onChange={(mode) => updateInvocation({ mode })}
                />
                <p style={{ margin: '12px 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
                    {invocation.mode === 'prefix' && 'Bot only responds to prefix commands like !help'}
                    {invocation.mode === 'mention' && 'Bot only responds when mentioned like @BotName help'}
                    {invocation.mode === 'hybrid' && 'Bot responds to both prefix commands and mentions'}
                </p>
            </div>

            {/* Live Preview */}
            <div className="form-group">
                <label className="form-label">Live Preview</label>
                <div
                    className="neu-inset"
                    style={{
                        padding: '16px',
                        borderRadius: '12px',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '14px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px'
                    }}
                >
                    <div style={{ color: 'var(--text-secondary)' }}>
                        <span style={{ color: 'var(--accent)' }}>{invocation.prefix}</span>help
                        <span style={{ marginLeft: '12px', opacity: 0.5 }}>→ Show help menu</span>
                    </div>
                    {invocation.mentionEnabled && (
                        <div style={{ color: 'var(--text-secondary)' }}>
                            <span style={{ color: 'var(--discord-blurple)' }}>@{botConfig.identity.username}</span> hello
                            <span style={{ marginLeft: '12px', opacity: 0.5 }}>→ Greet the user</span>
                        </div>
                    )}
                    {invocation.customTag && (
                        <div style={{ color: 'var(--text-secondary)' }}>
                            <span style={{ color: 'var(--accent)' }}>{invocation.customTag}</span>ask What is AI?
                            <span style={{ marginLeft: '12px', opacity: 0.5 }}>→ Ask a question</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
