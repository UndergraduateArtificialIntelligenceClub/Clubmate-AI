import React from 'react';

export const Input = ({ label, ...props }) => {
  return (
    <div style={{ marginBottom: '16px' }}>
      {label && <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>{label}</label>}
      <input 
        className="neu-inset"
        style={{
          width: '100%', padding: '12px 16px', border: 'none', outline: 'none',
          background: 'transparent', color: 'var(--text-main)', fontSize: '15px', boxSizing: 'border-box'
        }} 
        {...props} 
      />
    </div>
  );
};
