import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import './styles/theme.css';
import './components/global/components.css';
import { AuthProvider } from './context/AuthContext';
import { BotProvider } from './context/BotContext';
import { ToastProvider } from './components/global/ToastContext';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <BotProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </BotProvider>
    </AuthProvider>
  </React.StrictMode>
);

