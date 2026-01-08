import React from 'react';

export const Button = ({ children, onClick, variant = 'primary', style, disabled, className = '' }) => {
  const variantStyles = {
    danger: { color: 'var(--danger)' },
    success: { color: 'var(--success)' },
    primary: { color: 'var(--accent)' }
  };

  return (
    <button 
      className={`neu-outset neu-btn ${className}`} 
      onClick={onClick} 
      disabled={disabled}
      style={{ padding: '10px 20px', fontSize: '14px', ...variantStyles[variant], ...style }}
    >
      {children}
    </button>
  );
};
