import React, { useState, useEffect } from 'react';
import { Moon, Sun, Bell } from 'lucide-react';
import { useLocation } from 'react-router-dom';

export const Topbar = () => {
  const [theme, setTheme] = useState(localStorage.getItem('app-theme') || 'light');
  const location = useLocation();

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  const getTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard Overview';
    if (path.includes('api-keys')) return 'API Key Vault';
    if (path.includes('google')) return 'Google Services';
    if (path.includes('files')) return 'File Manager';
    if (path.includes('contacts')) return 'User Management';
    return 'Panel';
  };

  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '24px', color: 'var(--text-main)' }}>{getTitle()}</h1>
        <p style={{ margin: '4px 0 0 0', color: 'var(--text-secondary)', fontSize: '14px' }}>Welcome back, Administrator.</p>
      </div>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        <button className="neu-outset neu-btn" style={{ borderRadius: '50%', width: '44px', height: '44px', padding: 0 }}>
          <Bell size={20} />
        </button>
        <button 
          className="neu-outset neu-btn" 
          style={{ borderRadius: '50%', width: '44px', height: '44px', padding: 0 }}
          onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
        >
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>
    </header>
  );
};
