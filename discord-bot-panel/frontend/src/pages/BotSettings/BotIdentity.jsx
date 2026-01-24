import React, { useRef } from 'react';
import { Camera, User } from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { Select } from '../../components/global/Select';
import { StatusDot } from '../../components/global/Badge';

const statusOptions = [
    { value: 'online', label: 'Online' },
    { value: 'idle', label: 'Idle' },
    { value: 'dnd', label: 'Do Not Disturb' },
    { value: 'offline', label: 'Invisible' },
];

export default function BotIdentity() {
    const { botConfig, updateIdentity } = useBot();
    const { identity } = botConfig;
    const fileInputRef = useRef(null);

    const handleAvatarChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                updateIdentity({ avatarUrl: e.target.result });
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '40px', alignItems: 'start' }}>
            {/* Avatar Upload */}
            <div className="avatar-upload">
                {identity.avatarUrl ? (
                    <img src={identity.avatarUrl} alt="Bot Avatar" className="avatar-preview" />
                ) : (
                    <div
                        className="avatar-preview"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'var(--glass-bg)',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        <User size={48} />
                    </div>
                )}
                <div
                    className="avatar-upload-overlay"
                    onClick={() => fileInputRef.current?.click()}
                >
                    <Camera size={24} color="white" />
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={handleAvatarChange}
                />
            </div>

            {/* Identity Fields */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Bot Name */}
                <div className="form-group">
                    <label className="form-label">Bot Name</label>
                    <input
                        type="text"
                        className="form-input"
                        value={identity.name}
                        onChange={(e) => updateIdentity({ name: e.target.value })}
                        placeholder="Enter bot name"
                    />
                </div>

                {/* Username */}
                <div className="form-group">
                    <label className="form-label">Username / Handle</label>
                    <input
                        type="text"
                        className="form-input"
                        value={identity.username}
                        onChange={(e) => updateIdentity({ username: e.target.value })}
                        placeholder="bot_username"
                    />
                </div>

                {/* Status */}
                <div className="form-group">
                    <label className="form-label">Bot Status</label>
                    <Select
                        value={identity.status}
                        onChange={(value) => updateIdentity({ status: value })}
                        options={statusOptions}
                        renderValue={(opt) => (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <StatusDot status={opt.value} />
                                <span>{opt.label}</span>
                            </div>
                        )}
                        renderOption={(opt) => (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <StatusDot status={opt.value} />
                                <span>{opt.label}</span>
                            </div>
                        )}
                    />
                </div>

                {/* Bio */}
                <div className="form-group">
                    <label className="form-label">Bot Description / Bio</label>
                    <textarea
                        className="form-input form-textarea"
                        value={identity.bio}
                        onChange={(e) => updateIdentity({ bio: e.target.value })}
                        placeholder="Describe what your bot does..."
                        rows={4}
                    />
                </div>
            </div>
        </div>
    );
}
