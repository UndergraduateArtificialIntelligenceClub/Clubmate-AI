import React from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';
import { Sidebar } from './components/global/Sidebar';
import { Topbar } from './components/global/Topbar';

// Existing Pages
import Login from './pages/Login';
import Setup from './pages/Setup';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';
import APIKeys from './pages/APIKeys';
import Accounts from './pages/Accounts';

import Files from './pages/Files';
import Contacts from './pages/Contacts';
import { ProtectedRoute } from './components/global/ProtectedRoute';

// New Bot Management Pages
import BotSettings from './pages/BotSettings';
import ChatTesting from './pages/ChatTesting';
import RequestLogs from './pages/RequestLogs';

const AppLayout = () => (
  <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-color)' }}>
    <Sidebar />
    <main style={{ flex: 1, padding: '32px 40px', height: '100vh', overflowY: 'auto' }}>
      <Topbar />
      <Outlet />
    </main>
  </div>
);

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  { path: '/setup', element: <Setup /> },
  { path: '/auth/callback', element: <AuthCallback /> },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <Dashboard /> },
          { path: '/api-keys', element: <APIKeys /> },
          { path: '/accounts', element: <Accounts /> },
          { path: '/files', element: <Files /> },
          { path: '/contacts', element: <Contacts /> },
          // New Bot Management Routes
          { path: '/bot-settings', element: <BotSettings /> },
          { path: '/chat-testing', element: <ChatTesting /> },
          { path: '/request-logs', element: <RequestLogs /> },
        ]
      }
    ]
  }
]);


