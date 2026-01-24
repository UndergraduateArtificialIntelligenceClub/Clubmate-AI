import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, Key, Users, Folder, Settings, LogOut, Command,
  Bot, MessageSquare, FileText, User
} from 'lucide-react';


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

const NavSection = ({ title, children }) => (
  <div style={{ marginBottom: '16px' }}>
    <div style={{
      fontSize: '11px',
      fontWeight: 600,
      color: 'var(--text-secondary)',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      padding: '0 16px 8px',
      marginTop: '16px'
    }}>
      {title}
    </div>
    {children}
  </div>
);

export const Sidebar = () => {
  return (
    <aside className="neu-outset" style={{ width: '260px', height: '100vh', display: 'flex', flexDirection: 'column', padding: '24px', borderRadius: 0, zIndex: 50 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '32px', paddingLeft: '8px' }}>
        <div className="neu-outset" style={{ padding: '8px', borderRadius: '8px', color: 'var(--accent)' }}>
          <Command size={24} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: 'var(--text-main)' }}>BotPanel</h2>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Admin Console</span>
        </div>
      </div>

      <nav style={{ flex: 1, overflowY: 'auto' }}>
        <NavItem to="/" icon={Home} label="Dashboard" />

        {/* Bot Management Section */}
        <NavSection title="Bot Management">
          <NavItem to="/bot-settings" icon={Bot} label="Bot Settings" />
          <NavItem to="/chat-testing" icon={MessageSquare} label="Chat Testing" />
          <NavItem to="/request-logs" icon={FileText} label="Request Logs" />
        </NavSection>

        {/* Data & Storage Section */}
        <NavSection title="Data & Storage">
          <NavItem to="/contacts" icon={Users} label="Contacts" />
          <NavItem to="/files" icon={Folder} label="Files" />
          <NavItem to="/api-keys" icon={Key} label="API Vault" />
        </NavSection>

        {/* Settings Section */}
        <NavSection title="Settings">
          <NavItem to="/accounts" icon={User} label="Accounts" />
        </NavSection>
      </nav>


      <button className="neu-outset neu-btn" style={{ width: '100%', color: 'var(--danger)', marginTop: '20px' }}>
        <LogOut size={18} style={{ marginRight: '8px' }} /> Logout
      </button>
    </aside>
  );
};

