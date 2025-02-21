import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

export function LoginForm() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [isValid, setIsValid] = useState(false);
  const { login, error, isAuthenticating } = useAuth();

  useEffect(() => {
    validateForm();
  }, [formData]);

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    setValidationErrors(errors);
    setIsValid(Object.keys(errors).length === 0);

  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) return;
    await login(formData.email.trim(), formData.password.trim());
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-sm text-gray-400">
          Email
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Enter your email"
          className={cn(
            "px-3 py-2 bg-gray-800 border rounded-md text-sm",
            "text-gray-200 placeholder-gray-500",
            "focus:outline-none focus:ring-2 focus:ring-blue-500/50",
            "transition-colors duration-200",
            "border-gray-600",
            "focus:border-blue-500/50",
            "has-[:focus]:border-blue-500/50",
            validationErrors.email && formData.email && "border-red-500"
          )}
          aria-invalid={!!validationErrors.email}
          aria-describedby={validationErrors.email ? 'email-error' : undefined}
        />
        {validationErrors.email && (
          <span id="email-error" className="text-sm text-red-500 mt-1">
            {validationErrors.email}
          </span>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-sm text-gray-400">
          Password
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
            className={cn(
              "w-full px-3 py-2 bg-gray-800 border rounded-md text-sm",
              "text-gray-200 placeholder-gray-500",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50",
              "transition-colors duration-200 pr-10",
              "border-gray-600",
              "focus:border-blue-500/50",
              "has-[:focus]:border-blue-500/50",
              validationErrors.password && formData.password && "border-red-500"
            )}
            aria-invalid={!!validationErrors.password}
            aria-describedby={validationErrors.password ? 'password-error' : undefined}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 focus:outline-none"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {validationErrors.password && (
          <span id="password-error" className="text-sm text-red-500 mt-1">
            {validationErrors.password}
          </span>
        )}
      </div>
      {error && (
        <Alert variant="destructive" className="bg-red-900/30 border border-red-900/50 text-red-200">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <button
        type="submit"
        disabled={isAuthenticating || !isValid}
        className="px-4 py-2 bg-blue-600 text-gray-100 rounded-md text-sm 
                 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 
                 disabled:cursor-not-allowed transition-all duration-200"
      >
        {isAuthenticating ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}