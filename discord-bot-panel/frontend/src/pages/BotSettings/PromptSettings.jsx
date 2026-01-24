import React from 'react';
import { Sparkles } from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { Slider } from '../../components/global/Slider';
import { Tabs } from '../../components/global/Tabs';

const personalityPresets = [
    { id: 'friendly', label: 'Friendly', icon: '😊' },
    { id: 'professional', label: 'Professional', icon: '💼' },
    { id: 'sarcastic', label: 'Sarcastic', icon: '😏' },
    { id: 'custom', label: 'Custom', icon: '✨' },
];

const presetPrompts = {
    friendly: 'You are a friendly and enthusiastic Discord bot. You love helping users and always respond with warmth and positivity. Use casual language, emojis occasionally, and make users feel welcome.',
    professional: 'You are a professional and efficient Discord bot. Provide clear, concise, and helpful responses. Maintain a formal tone while being approachable. Focus on delivering accurate information.',
    sarcastic: 'You are a witty Discord bot with a sarcastic sense of humor. While still being helpful, you can include playful jokes and clever remarks. Keep it light-hearted and never mean-spirited.',
    custom: '',
};

export default function PromptSettings() {
    const { botConfig, updatePrompt } = useBot();
    const { prompt } = botConfig;

    const handlePresetChange = (personality) => {
        if (personality === 'custom') {
            updatePrompt({ personality });
        } else {
            updatePrompt({
                personality,
                systemPrompt: presetPrompts[personality]
            });
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {/* Personality Presets */}
            <div className="form-group">
                <label className="form-label">Personality Preset</label>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    {personalityPresets.map((preset) => (
                        <button
                            key={preset.id}
                            onClick={() => handlePresetChange(preset.id)}
                            className="neu-outset"
                            style={{
                                padding: '14px 24px',
                                borderRadius: '12px',
                                border: 'none',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                fontWeight: 500,
                                color: prompt.personality === preset.id ? 'var(--accent)' : 'var(--text-secondary)',
                                boxShadow: prompt.personality === preset.id
                                    ? 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)'
                                    : undefined,
                                transition: 'all 150ms ease',
                            }}
                        >
                            <span style={{ fontSize: '18px' }}>{preset.icon}</span>
                            {preset.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* System Prompt */}
            <div className="form-group">
                <label className="form-label">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Sparkles size={14} />
                        System Prompt
                    </div>
                </label>
                <textarea
                    className="form-input form-textarea"
                    value={prompt.systemPrompt}
                    onChange={(e) => updatePrompt({ systemPrompt: e.target.value, personality: 'custom' })}
                    placeholder="Define your bot's personality and behavior..."
                    rows={6}
                    style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '13px',
                        lineHeight: 1.6
                    }}
                />
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    This prompt is sent with every AI request to define your bot's behavior
                </span>
            </div>

            {/* Tone Sliders */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
                <div className="form-group">
                    <label className="form-label">Response Tone</label>
                    <Slider
                        value={prompt.toneFormality}
                        onChange={(value) => updatePrompt({ toneFormality: value })}
                        min={0}
                        max={100}
                        leftLabel="Casual"
                        rightLabel="Formal"
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">Response Length</label>
                    <Slider
                        value={prompt.responseLength}
                        onChange={(value) => updatePrompt({ responseLength: value })}
                        min={0}
                        max={100}
                        leftLabel="Short"
                        rightLabel="Detailed"
                    />
                </div>
            </div>

            {/* Preview */}
            <div className="form-group">
                <label className="form-label">Behavior Preview</label>
                <div
                    className="neu-inset"
                    style={{
                        padding: '20px',
                        borderRadius: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                        <div
                            style={{
                                width: '40px',
                                height: '40px',
                                borderRadius: '50%',
                                background: 'var(--discord-blurple)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontSize: '16px',
                                fontWeight: 600,
                                flexShrink: 0
                            }}
                        >
                            {botConfig.identity.name.charAt(0)}
                        </div>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{botConfig.identity.name}</span>
                                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Today at 12:00 PM</span>
                            </div>
                            <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.5, color: 'var(--text-main)' }}>
                                {prompt.personality === 'friendly' && "Hey there! 👋 I'm so happy you're here! How can I help make your day better?"}
                                {prompt.personality === 'professional' && "Hello. I'm ready to assist you. Please let me know how I can help."}
                                {prompt.personality === 'sarcastic' && "Oh, another human. What can I possibly help you with this time? 😏"}
                                {prompt.personality === 'custom' && "This is a preview of how your bot might respond based on your custom prompt."}
                            </p>
                        </div>
                    </div>

                    <div style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        padding: '12px',
                        background: 'var(--glass-bg)',
                        borderRadius: '8px',
                        marginTop: '8px'
                    }}>
                        <strong>Response Style:</strong>{' '}
                        {prompt.toneFormality < 33 ? 'Very casual' : prompt.toneFormality < 66 ? 'Balanced' : 'Formal'} •
                        {prompt.responseLength < 33 ? ' Concise' : prompt.responseLength < 66 ? ' Standard' : ' Detailed'} responses
                    </div>
                </div>
            </div>
        </div>
    );
}
