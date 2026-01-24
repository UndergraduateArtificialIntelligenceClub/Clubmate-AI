import React from 'react';
import { Bot, User, Shield, Crown, AlertCircle, Clock } from 'lucide-react';

const modeIcons = {
    user: User,
    moderator: Shield,
    admin: Crown,
};

const modeColors = {
    user: 'var(--discord-blurple)',
    moderator: 'var(--status-idle)',
    admin: 'var(--discord-red)',
};

export default function ChatMessage({ message, botConfig, testMode }) {
    const isBot = message.type === 'bot';
    const ModeIcon = testMode ? modeIcons[testMode] : User;

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Simple markdown-like parsing
    const formatContent = (content) => {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`(.*?)`/g, '<code style="background: var(--glass-bg); padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>')
            .replace(/\n/g, '<br/>');
    };

    return (
        <div className={`chat-message ${isBot ? 'bot' : 'user'}`}>
            {/* Avatar */}
            <div
                className="chat-avatar"
                style={{
                    background: isBot
                        ? 'linear-gradient(135deg, var(--discord-blurple), var(--accent))'
                        : modeColors[testMode] || 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    flexShrink: 0
                }}
            >
                {isBot ? <Bot size={20} /> : <ModeIcon size={18} />}
            </div>

            {/* Content */}
            <div className="chat-content" style={{ textAlign: isBot ? 'left' : 'right' }}>
                <div className="chat-header" style={{ justifyContent: isBot ? 'flex-start' : 'flex-end' }}>
                    <span className="chat-username" style={{ color: isBot ? 'var(--accent)' : modeColors[testMode] }}>
                        {isBot ? botConfig?.identity?.name || 'Bot' : `Test User (${testMode})`}
                    </span>
                    <span className="chat-timestamp">{formatTime(message.timestamp)}</span>
                    {message.executionTime && (
                        <span style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '11px',
                            color: 'var(--text-secondary)'
                        }}>
                            <Clock size={10} />
                            {message.executionTime}ms
                        </span>
                    )}
                </div>

                <div
                    className="chat-text"
                    style={{
                        color: message.isError ? 'var(--discord-red)' : 'var(--text-main)',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '8px',
                        justifyContent: isBot ? 'flex-start' : 'flex-end'
                    }}
                >
                    {message.isError && <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />}
                    <span dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
                </div>
            </div>
        </div>
    );
}
