import React from 'react';
import '../../styles/theme.css';

export const NeomorphicCard = ({ children, title, className = '', style, actions }) => {
  return (
    <div className={`neu-outset ${className}`} style={{ padding: '24px', display: 'flex', flexDirection: 'column', ...style }}>
      {(title || actions) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          {title && <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-main)' }}>{title}</h3>}
          {actions && <div>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
