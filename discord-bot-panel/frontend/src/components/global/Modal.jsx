import React from 'react';
import { X } from 'lucide-react';

export const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(2px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="neu-outset" style={{ width: '500px', maxWidth: '90%', padding: '24px', background: 'var(--bg-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>{title}</h3>
          <button onClick={onClose} className="neu-btn" style={{ padding: '6px', borderRadius: '50%' }}><X size={18}/></button>
        </div>
        {children}
      </div>
    </div>
  );
};
