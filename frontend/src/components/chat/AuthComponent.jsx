import { useState } from 'react';
import { useAuth } from './AuthContext';
import { LogOut } from 'lucide-react';
import { AuthTabs } from './AuthTabs';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export function AuthComponent() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();

  if (isAuthenticated && user) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">{user.email}</span>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 text-gray-100 rounded-md text-sm 
                   hover:bg-gray-700 transition-all duration-200"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        onClick={() => setShowAuthModal(true)}
        className="px-3 py-1.5 bg-blue-600 text-gray-100 rounded-md text-sm 
                 hover:bg-blue-500 transition-all duration-200"
      >
        Login / Register
      </button>

      {showAuthModal && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/50 z-[100]"
            onClick={() => setShowAuthModal(false)}
          />
          {/* Modal */}
          <div 
            className="fixed left-1/2 top-20 -translate-x-1/2 z-[101] w-full max-w-md mx-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="auth-modal-title"
            aria-describedby="auth-modal-description"
          >
            <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 id="auth-modal-title" className="text-xl font-semibold text-gray-100">Authentication</h2>
                <button
                  onClick={() => setShowAuthModal(false)}
                  className="text-gray-400 hover:text-gray-300"
                  aria-label="Close authentication dialog"
                >
                  ✕
                </button>
              </div>
              <div id="auth-modal-description" className="sr-only">
                Login or register to access the chat interface
              </div>
              <AuthTabs onClose={() => setShowAuthModal(false)} />
            </div>
          </div>
        </>
      )}
    </>
  );
}