import { useState } from 'react';
import { useAuth } from './chat/AuthContext';
import { Info, X } from 'lucide-react';

// SVG pattern for the background
const BackgroundPattern = () => (
  <svg className="absolute inset-0 -z-10 h-full w-full stroke-[#333333]/25 [mask-image:radial-gradient(100%_100%_at_top_center,white,transparent)]">
    <defs>
      <pattern
        id="hexagons"
        width="50"
        height="86.6"
        patternUnits="userSpaceOnUse"
        patternTransform="scale(0.5) rotate(0)"
      >
        <path d="M25,0 L50,43.3 L25,86.6 L0,43.3 Z M25,86.6 L50,43.3 L75,86.6 L50,129.9 Z M25,86.6 L0,43.3 L-25,86.6 L0,129.9 Z" />
      </pattern>
    </defs>
    <rect width="100%" height="100%" strokeWidth="0" fill="url(#hexagons)" />
  </svg>
);

// Modal component for Terms and Privacy
const Modal = ({ title, content, onClose }) => {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-[#1A1A1A] border border-[#333333] rounded-[var(--radius-lg)] 
                    max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-xl">
        <div className="flex justify-between items-center p-6 border-b border-[#333333]">
          <h2 className="text-xl font-medium text-white">{title}</h2>
          <button onClick={onClose} className="text-[#999999] hover:text-white">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 overflow-y-auto">
          <div className="prose prose-invert">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
};

const TermsContent = () => (
  <div className="space-y-4 text-[#999999]">
    <p>Welcome to the GtRNAdb Expert Chatbot. By using our service, you agree to these terms:</p>
    
    <h3 className="text-white font-medium">1. Service Description</h3>
    <p>This is an AI-powered research assistant designed to help researchers and students explore and understand tRNA data from GtRNAdb.</p>
    
    <h3 className="text-white font-medium">2. Data Usage</h3>
    <p>We only collect and use data necessary to provide you with the service and comply with legal requirements. </p>
    
    <h3 className="text-white font-medium">3. User Responsibilities</h3>
    <p>Users are responsible for maintaining the confidentiality of their account credentials and using the service in compliance with regulations.</p>
    
    <h3 className="text-white font-medium">4. Limitations</h3>
    <p>The service is provided "as is" without warranties. We strive for accuracy but cannot guarantee the completeness or accuracy of all information.</p>
  </div>
);

const PrivacyContent = () => (
  <div className="space-y-4 text-[#999999]">
    <p>Your privacy is important to us. This policy explains how we handle your data:</p>
    
    <h3 className="text-white font-medium">1. Data Collection</h3>
    <p>We collect only essential data required to provide the service, including email addresses for authentication and chat history for continuity of service.</p>
    
    <h3 className="text-white font-medium">2. Data Control</h3>
    <p>The instance administrator has control over all data stored in the system. Data is stored securely and used only for providing and improving the service.</p>
    
    <h3 className="text-white font-medium">3. Data Usage</h3>
    <p>Your data is used solely for:</p>
    <ul className="list-disc pl-5 space-y-2">
      <li>Providing and maintaining the service</li>
      <li>Improving user experience</li>
      <li>Complying with legal requirements</li>
    </ul>
    
    <h3 className="text-white font-medium">4. Data Protection</h3>
    <p>We implement appropriate security measures to protect your data against unauthorized access or disclosure.</p>
  </div>
);

export function LandingPage() {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const { login, register, error: authError, isAuthenticating } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    acceptedTerms: false
  });
  const [error, setError] = useState('');
  const [showTerms, setShowTerms] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validations
    if (!isLoginMode) {
      if (!formData.acceptedTerms) {
        setError('Please accept the terms and conditions to continue');
        return;
      }
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match');
        return;
      }
    }

    // Attempt login/register
    const success = isLoginMode 
      ? await login(formData.email, formData.password)
      : await register(formData.email, formData.password);

    // If there was an auth error, it will be in authError
    if (!success && authError) {
      setError(authError);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F0F] flex flex-col items-center justify-center px-4 relative">
      {/* Background Pattern */}
      <BackgroundPattern />
      
      {/* Gradient Line */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#FF6F61]/0 via-[#FF6F61] to-[#FF6F61]/0" />
      
      {/* Main Content */}
      <div className="w-full max-w-[400px] space-y-8">
        {/* Logo/Title */}
        <div className="text-center space-y-4">
          <h1 className="text-3xl text-white font-medium tracking-tight">
            GtRNAdb Expert
          </h1>
          <div className="space-y-2">
            <p className="text-[#999999] text-lg leading-relaxed">
              Your AI research companion for exploring tRNA biology
            </p>
            <p className="text-[#666666] text-sm leading-relaxed max-w-[300px] mx-auto">
              Access expert knowledge about tRNA sequences, structures, and genomic contexts
            </p>
          </div>
        </div>

        {/* Auth Form */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-sm border border-[#333333] rounded-[var(--radius-lg)] p-6">
          {/* Mode Toggle */}
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setIsLoginMode(true)}
              className={`text-sm font-medium ${
                isLoginMode 
                  ? 'text-white' 
                  : 'text-[#999999] hover:text-white transition-colors'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsLoginMode(false)}
              className={`text-sm font-medium ${
                !isLoginMode 
                  ? 'text-white' 
                  : 'text-[#999999] hover:text-white transition-colors'
              }`}
            >
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm text-[#999999] mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-[#252525] border border-[#333333] rounded-[var(--radius-md)]
                         px-3 py-2 text-white placeholder-[#666666] text-sm
                         focus:outline-none focus:ring-1 focus:ring-[#FF6F61]
                         hover:border-[#666666] transition-colors"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm text-[#999999] mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full bg-[#252525] border border-[#333333] rounded-[var(--radius-md)]
                         px-3 py-2 text-white placeholder-[#666666] text-sm
                         focus:outline-none focus:ring-1 focus:ring-[#FF6F61]
                         hover:border-[#666666] transition-colors"
                required
              />
            </div>

            {!isLoginMode && (
              <>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm text-[#999999] mb-1.5">
                    Confirm Password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className="w-full bg-[#252525] border border-[#333333] rounded-[var(--radius-md)]
                             px-3 py-2 text-white placeholder-[#666666] text-sm
                             focus:outline-none focus:ring-1 focus:ring-[#FF6F61]
                             hover:border-[#666666] transition-colors"
                    required
                  />
                </div>

                <div className="pt-2">
                  <label className="flex items-start gap-3 cursor-pointer group text-sm">
                    <div className="relative pt-0.5">
                      <input
                        type="checkbox"
                        checked={formData.acceptedTerms}
                        onChange={(e) => setFormData({ ...formData, acceptedTerms: e.target.checked })}
                        className="peer sr-only"
                      />
                      <div className="h-4 w-4 border border-[#666666] rounded-[var(--radius-sm)]
                                  group-hover:border-[#999999] peer-checked:border-[#FF6F61]
                                  peer-checked:bg-[#FF6F61] transition-colors">
                      </div>
                    </div>
                    <span className="text-[#999999] group-hover:text-white transition-colors">
                      I accept the{' '}
                      <button 
                        type="button"
                        onClick={() => setShowTerms(true)}
                        className="text-[#FF6F61] hover:text-[#FF6F61]/80"
                      >
                        Terms of Service
                      </button>
                      {' '}and{' '}
                      <button
                        type="button"
                        onClick={() => setShowPrivacy(true)}
                        className="text-[#FF6F61] hover:text-[#FF6F61]/80"
                      >
                        Privacy Policy
                      </button>
                    </span>
                  </label>
                </div>
              </>
            )}

            {(error || authError) && (
              <div className="flex items-start gap-2 text-sm text-[#FF6F61] bg-[#FF6F61]/10 
                           border border-[#FF6F61]/20 rounded-[var(--radius-md)] p-3 animate-in fade-in">
                <Info size={16} className="mt-0.5 flex-shrink-0" />
                <span>{error || authError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full bg-white text-[#0F0F0F] rounded-[var(--radius-md)] py-2 px-4
                       text-sm font-medium hover:bg-white/90 transition-colors mt-6
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAuthenticating 
                ? (isLoginMode ? 'Signing In...' : 'Creating Account...') 
                : (isLoginMode ? 'Sign In' : 'Create Account')}
            </button>
          </form>
        </div>

        {/* Footer Links */}
        <div className="text-center">
          <a href="#" className="text-sm text-[#999999] hover:text-white transition-colors">
            Need help?
          </a>
        </div>
      </div>

      {/* Terms Modal */}
      {showTerms && (
        <Modal
          title="Terms of Service"
          content={<TermsContent />}
          onClose={() => setShowTerms(false)}
        />
      )}

      {/* Privacy Modal */}
      {showPrivacy && (
        <Modal
          title="Privacy Policy"
          content={<PrivacyContent />}
          onClose={() => setShowPrivacy(false)}
        />
      )}
    </div>
  );
}