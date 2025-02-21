import { useState, useEffect } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { useAuth } from './AuthContext';

export function AuthTabs({ onClose }) {
  const [activeTab, setActiveTab] = useState('login');
  const { isAuthenticated } = useAuth();

  // Close modal when authentication is successful
  useEffect(() => {
    if (isAuthenticated && onClose) {
      onClose();
    }
  }, [isAuthenticated, onClose]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 bg-gray-800 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('login')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
            activeTab === 'login'
              ? 'bg-blue-600 text-gray-100'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Login
        </button>
        <button
          onClick={() => setActiveTab('register')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
            activeTab === 'register'
              ? 'bg-blue-600 text-gray-100'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Register
        </button>
      </div>
      <div className="mt-4">
        {activeTab === 'login' ? <LoginForm /> : <RegisterForm />}
      </div>
    </div>
  );
}