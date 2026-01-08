import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Key, Users, Folder, Settings, LogOut, Command } from 'lucide-react';

const NavItem = ({ to, icon: Icon, label }) => (
  <NavLink 
    to={to} 
    style={({ isActive }) => ({
      display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 16px',
      textDecoration: 'none', borderRadius: '12px', marginBottom: '8px',
      color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
      background: isActive ? 'var(--bg-color)' : 'transparent',
      boxShadow: isActive ? 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)' : 'none',
      transition: 'all 0.2s'
    })}
  >
    <Icon size={20} />
    <span style={{ fontWeight: 500 }}>{label}</span>
  </NavLink>
);

export const Sidebar = () => {
  return (
    <aside className="neu-outset" style={{ width: '260px', height: '100vh', display: 'flex', flexDirection: 'column', padding: '24px', borderRadius: 0, zIndex: 50 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '40px', paddingLeft: '8px' }}>
        <div className="neu-outset" style={{ padding: '8px', borderRadius: '8px', color: 'var(--accent)' }}>
          <Command size={24} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: 'var(--text-main)' }}>BotPanel</h2>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Admin Console</span>
        </div>
      </div>

      <nav style={{ flex: 1 }}>
        <NavItem to="/" icon={Home} label="Dashboard" />
        <NavItem to="/contacts" icon={Users} label="Contacts" />
        <NavItem to="/files" icon={Folder} label="Files" />
        <NavItem to="/api-keys" icon={Key} label="API Vault" />
        <NavItem to="/google" icon={Settings} label="Google Integration" />
      </nav>

      <button className="neu-outset neu-btn" style={{ width: '100%', color: 'var(--danger)', marginTop: '20px' }}>
        <LogOut size={18} style={{ marginRight: '8px' }} /> Logout
      </button>
    </aside>
  );
};
