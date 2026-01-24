import React from 'react';
import { CheckCircle, AlertCircle, Clock, Info, XCircle } from 'lucide-react';

const variants = {
    success: { className: 'badge-success', icon: CheckCircle },
    warning: { className: 'badge-warning', icon: Clock },
    error: { className: 'badge-error', icon: XCircle },
    info: { className: 'badge-info', icon: Info },
    neutral: { className: 'badge-neutral', icon: null },
};

export const Badge = ({ variant = 'neutral', children, icon: CustomIcon }) => {
    const config = variants[variant] || variants.neutral;
    const Icon = CustomIcon || config.icon;

    return (
        <span className={`badge ${config.className}`}>
            {Icon && <Icon size={12} />}
            {children}
        </span>
    );
};

export const StatusDot = ({ status = 'offline' }) => (
    <span className={`status-dot ${status}`} />
);

export default Badge;
