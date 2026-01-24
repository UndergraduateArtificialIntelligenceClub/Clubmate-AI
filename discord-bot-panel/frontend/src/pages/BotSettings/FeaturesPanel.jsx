import React, { useState } from 'react';
import {
    MessageSquare, Shield, Reply, FileText, BarChart2,
    Bell, ChevronDown, ChevronUp, Settings
} from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { Toggle } from '../../components/global/Toggle';
import { Select } from '../../components/global/Select';

const features = [
    {
        key: 'aiChat',
        name: 'AI Chat',
        description: 'Enable intelligent conversations with AI-powered responses',
        icon: MessageSquare,
        settings: [
            {
                key: 'model', label: 'AI Model', type: 'select', options: [
                    { value: 'gpt-4', label: 'GPT-4 (Recommended)' },
                    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                    { value: 'claude-3', label: 'Claude 3' },
                ]
            },
            { key: 'maxTokens', label: 'Max Response Tokens', type: 'number', min: 256, max: 4096 },
        ],
    },
    {
        key: 'moderation',
        name: 'Moderation',
        description: 'Automated moderation tools and content filtering',
        icon: Shield,
        settings: [
            { key: 'autoMod', label: 'Auto-Moderation', type: 'toggle' },
            { key: 'profanityFilter', label: 'Profanity Filter', type: 'toggle' },
        ],
    },
    {
        key: 'autoReplies',
        name: 'Auto-Replies',
        description: 'Automatic responses based on custom trigger rules',
        icon: Reply,
    },
    {
        key: 'logging',
        name: 'Logging',
        description: 'Log bot activities and moderation actions',
        icon: FileText,
        settings: [
            { key: 'channel', label: 'Log Channel', type: 'text', placeholder: '#bot-logs' },
        ],
    },
    {
        key: 'serverAnalytics',
        name: 'Server Analytics',
        description: 'Track server activity and member engagement',
        icon: BarChart2,
    },
    {
        key: 'welcomeMessages',
        name: 'Welcome Messages',
        description: 'Send customized welcome messages to new members',
        icon: Bell,
        settings: [
            { key: 'channel', label: 'Welcome Channel', type: 'text', placeholder: '#welcome' },
            { key: 'message', label: 'Welcome Message', type: 'textarea', placeholder: 'Welcome to the server, {user}!' },
        ],
    },
];

const FeatureCard = ({ feature, config, onToggle, onUpdateSetting }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const Icon = feature.icon;
    const isEnabled = config?.enabled;

    return (
        <div className={`feature-card ${isEnabled ? 'active' : ''}`}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div
                        className="neu-inset"
                        style={{
                            padding: '12px',
                            borderRadius: '12px',
                            color: isEnabled ? 'var(--accent)' : 'var(--text-secondary)',
                            transition: 'color 250ms ease'
                        }}
                    >
                        <Icon size={22} />
                    </div>
                    <div>
                        <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>{feature.name}</h4>
                        <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                            {feature.description}
                        </p>
                    </div>
                </div>
                <Toggle checked={isEnabled} onChange={onToggle} />
            </div>

            {/* Advanced Settings */}
            {feature.settings && isEnabled && (
                <>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            background: 'none',
                            border: 'none',
                            padding: '8px 0',
                            color: 'var(--accent)',
                            fontSize: '13px',
                            cursor: 'pointer',
                            fontFamily: 'var(--font-main)',
                        }}
                    >
                        <Settings size={14} />
                        Advanced Settings
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {isExpanded && (
                        <div
                            className="animate-slideDown"
                            style={{
                                marginTop: '12px',
                                padding: '16px',
                                background: 'var(--glass-bg)',
                                borderRadius: '12px',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '16px'
                            }}
                        >
                            {feature.settings.map((setting) => (
                                <div key={setting.key} className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">{setting.label}</label>
                                    {setting.type === 'select' && (
                                        <Select
                                            value={config[setting.key]}
                                            onChange={(value) => onUpdateSetting(setting.key, value)}
                                            options={setting.options}
                                        />
                                    )}
                                    {setting.type === 'toggle' && (
                                        <Toggle
                                            checked={config[setting.key]}
                                            onChange={(checked) => onUpdateSetting(setting.key, checked)}
                                        />
                                    )}
                                    {setting.type === 'text' && (
                                        <input
                                            type="text"
                                            className="form-input"
                                            value={config[setting.key] || ''}
                                            onChange={(e) => onUpdateSetting(setting.key, e.target.value)}
                                            placeholder={setting.placeholder}
                                        />
                                    )}
                                    {setting.type === 'number' && (
                                        <input
                                            type="number"
                                            className="form-input"
                                            value={config[setting.key] || setting.min}
                                            onChange={(e) => onUpdateSetting(setting.key, parseInt(e.target.value))}
                                            min={setting.min}
                                            max={setting.max}
                                        />
                                    )}
                                    {setting.type === 'textarea' && (
                                        <textarea
                                            className="form-input form-textarea"
                                            value={config[setting.key] || ''}
                                            onChange={(e) => onUpdateSetting(setting.key, e.target.value)}
                                            placeholder={setting.placeholder}
                                            rows={3}
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default function FeaturesPanel() {
    const { botConfig, updateFeature } = useBot();

    return (
        <div className="feature-grid">
            {features.map((feature) => (
                <FeatureCard
                    key={feature.key}
                    feature={feature}
                    config={botConfig.features[feature.key]}
                    onToggle={() => updateFeature(feature.key, { enabled: !botConfig.features[feature.key]?.enabled })}
                    onUpdateSetting={(settingKey, value) => updateFeature(feature.key, { [settingKey]: value })}
                />
            ))}
        </div>
    );
}
