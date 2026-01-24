import React, { useState, useRef, useEffect } from 'react';
import {
    Send, RotateCcw, Download, Terminal,
    User, Shield, Crown, Bot
} from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { botApi } from '../../services/botApi';
import { useToast } from '../../components/global/ToastContext';
import { Tabs } from '../../components/global/Tabs';
import { Button } from '../../components/global/Button';
import ChatMessage from './ChatMessage';
import DebugPanel from './DebugPanel';

const testModes = [
    { id: 'user', label: 'User', icon: <User size={14} /> },
    { id: 'moderator', label: 'Moderator', icon: <Shield size={14} /> },
    { id: 'admin', label: 'Admin', icon: <Crown size={14} /> },
];

export default function ChatTesting() {
    const { botConfig } = useBot();
    const { addToast } = useToast();
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [testMode, setTestMode] = useState('user');
    const [isTyping, setIsTyping] = useState(false);
    const [debugData, setDebugData] = useState(null);
    const [showDebug, setShowDebug] = useState(true);

    // Initial bot greeting
    useEffect(() => {
        setMessages([{
            id: 'welcome',
            type: 'bot',
            content: `👋 Hello! I'm **${botConfig.identity.name}** in test mode. Try sending me a command or message!\n\nPrefix: \`${botConfig.invocation.prefix}\``,
            timestamp: new Date().toISOString(),
        }]);
    }, [botConfig.identity.name, botConfig.invocation.prefix]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isTyping) return;

        const userMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: inputValue,
            timestamp: new Date().toISOString(),
            testMode,
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsTyping(true);

        try {
            const response = await botApi.testBotMessage({
                message: inputValue,
                mode: testMode,
                invocationType: inputValue.startsWith(botConfig.invocation.prefix) ? 'prefix' : 'mention',
            });

            setDebugData(response.debug);

            const botMessage = {
                id: (Date.now() + 1).toString(),
                type: 'bot',
                content: response.error || response.response,
                timestamp: new Date().toISOString(),
                isError: !!response.error,
                executionTime: response.executionTime,
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            addToast('Failed to process message', 'error');
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                type: 'bot',
                content: 'Failed to process your message. Please try again.',
                timestamp: new Date().toISOString(),
                isError: true,
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleReset = () => {
        setMessages([{
            id: 'welcome',
            type: 'bot',
            content: `👋 Conversation reset! I'm **${botConfig.identity.name}** in test mode.`,
            timestamp: new Date().toISOString(),
        }]);
        setDebugData(null);
        inputRef.current?.focus();
    };

    const handleExport = () => {
        const exportData = {
            botName: botConfig.identity.name,
            testMode,
            timestamp: new Date().toISOString(),
            messages: messages.map(m => ({
                type: m.type,
                content: m.content,
                timestamp: m.timestamp,
            })),
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-test-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        addToast('Chat log exported', 'success');
    };

    return (
        <div className="animate-fadeIn" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
            {/* Header */}
            <div style={{ marginBottom: '24px' }}>
                <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 700 }}>Chat Testing</h1>
                <p style={{ margin: '8px 0 0', color: 'var(--text-secondary)' }}>
                    Test your bot's responses before deploying to Discord
                </p>
            </div>

            {/* Main Content */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: showDebug ? '1fr 380px' : '1fr', gap: '24px', minHeight: 0 }}>
                {/* Chat Panel */}
                <div
                    className="section-card"
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        padding: 0,
                        overflow: 'hidden'
                    }}
                >
                    {/* Chat Header */}
                    <div style={{
                        padding: '16px 24px',
                        borderBottom: '1px solid var(--glass-border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div
                                style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '50%',
                                    background: 'linear-gradient(135deg, var(--discord-blurple), var(--accent))',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white'
                                }}
                            >
                                <Bot size={22} />
                            </div>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>{botConfig.identity.name}</h3>
                                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Test Environment</span>
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Tabs
                                tabs={testModes}
                                activeTab={testMode}
                                onChange={setTestMode}
                            />
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className="chat-messages" style={{ flex: 1, overflow: 'auto' }}>
                        {messages.map((message) => (
                            <ChatMessage
                                key={message.id}
                                message={message}
                                botConfig={botConfig}
                                testMode={message.testMode}
                            />
                        ))}
                        {isTyping && (
                            <div className="chat-message bot">
                                <div
                                    className="chat-avatar"
                                    style={{
                                        background: 'linear-gradient(135deg, var(--discord-blurple), var(--accent))',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'white'
                                    }}
                                >
                                    <Bot size={20} />
                                </div>
                                <div className="typing-indicator">
                                    <span className="typing-dot"></span>
                                    <span className="typing-dot"></span>
                                    <span className="typing-dot"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="chat-input-area">
                        <div style={{ flex: 1, position: 'relative' }}>
                            <input
                                ref={inputRef}
                                type="text"
                                className="form-input"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={`Type a message... (prefix: ${botConfig.invocation.prefix})`}
                                style={{ width: '100%', paddingRight: '50px' }}
                                disabled={isTyping}
                            />
                        </div>
                        <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping}>
                            <Send size={18} />
                        </Button>
                    </div>

                    {/* Controls */}
                    <div style={{
                        padding: '12px 24px',
                        borderTop: '1px solid var(--glass-border)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <div style={{ display: 'flex', gap: '12px' }}>
                            <Button variant="ghost" onClick={handleReset}>
                                <RotateCcw size={16} /> Reset
                            </Button>
                            <Button variant="ghost" onClick={handleExport}>
                                <Download size={16} /> Export
                            </Button>
                        </div>
                        <Button
                            variant="ghost"
                            onClick={() => setShowDebug(!showDebug)}
                            style={{ color: showDebug ? 'var(--accent)' : 'var(--text-secondary)' }}
                        >
                            <Terminal size={16} /> Debug
                        </Button>
                    </div>
                </div>

                {/* Debug Panel */}
                {showDebug && (
                    <DebugPanel debugData={debugData} />
                )}
            </div>
        </div>
    );
}
