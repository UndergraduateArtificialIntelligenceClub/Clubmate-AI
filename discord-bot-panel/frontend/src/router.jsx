import React from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';
import { Sidebar } from './components/global/Sidebar';
import { Topbar } from './components/global/Topbar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import APIKeys from './pages/APIKeys';
import GoogleAuth from './pages/GoogleAuth'; // (Use code from previous response)
import Files from './pages/Files';           // (Use code from previous response)
import Contacts from './pages/Contacts';     // (Use code from previous response)

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
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/api-keys', element: <APIKeys /> },
      { path: '/google', element: <GoogleAuth /> },
      { path: '/files', element: <Files /> },
      { path: '/contacts', element: <Contacts /> },
    ]
  }
]);
