import { AuthProvider, useAuth } from './components/chat/AuthContext';
import { ChatProvider } from './components/chat/ChatContext';
import ChatInterface from './components/chat/ChatInterface';
import { LandingPage } from './components/LandingPage';

function AppContent() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? (
    <ChatProvider>
      <ChatInterface />
    </ChatProvider>
  ) : (
    <LandingPage />
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;