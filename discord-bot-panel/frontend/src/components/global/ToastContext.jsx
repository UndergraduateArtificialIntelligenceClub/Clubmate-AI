import React, { createContext, useState, useContext, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => removeToast(id), 3000);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div style={{
        position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
        display: 'flex', flexDirection: 'column', gap: '10px'
      }}>
        {toasts.map(toast => (
          <div key={toast.id} className="neu-outset" style={{
            padding: '12px 16px',
            borderRadius: '12px',
            background: 'var(--bg-color)',
            display: 'flex', alignItems: 'center', gap: '12px',
            borderLeft: `4px solid ${
              toast.type === 'success' ? 'var(--success)' :
              toast.type === 'error' ? 'var(--danger)' : 'var(--accent)'
            }`,
            animation: 'slideIn 0.3s ease'
          }}>
            {toast.type === 'success' && <CheckCircle size={18} color="var(--success)" />}
            {toast.type === 'error' && <AlertCircle size={18} color="var(--danger)" />}
            {toast.type === 'info' && <Info size={18} color="var(--accent)" />}
            <span style={{ fontSize: '14px', fontWeight: 500 }}>{toast.message}</span>
            <button onClick={() => removeToast(toast.id)} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 0, color: 'var(--text-secondary)' }}>
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </ToastContext.Provider>
  );
};
