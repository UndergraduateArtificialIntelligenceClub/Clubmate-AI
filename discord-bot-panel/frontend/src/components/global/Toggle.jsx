import React from 'react';

export const Toggle = ({ checked, onChange, label, description }) => {
    return (
        <div className="toggle-wrapper">
            <div
                className={`toggle-switch ${checked ? 'active' : ''}`}
                onClick={() => onChange(!checked)}
                role="switch"
                aria-checked={checked}
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onChange(!checked);
                    }
                }}
            />
            {(label || description) && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {label && (
                        <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>
                            {label}
                        </span>
                    )}
                    {description && (
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                            {description}
                        </span>
                    )}
                </div>
            )}
        </div>
    );
};

export default Toggle;
