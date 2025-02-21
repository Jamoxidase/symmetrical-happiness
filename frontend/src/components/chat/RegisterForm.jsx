import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Eye, EyeOff, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export function RegisterForm() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [isValid, setIsValid] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    requirements: {
      length: false,
      uppercase: false,
      lowercase: false,
      number: false,
      special: false
    }
  });
  const { register, error, isAuthenticating } = useAuth();

  useEffect(() => {
    validateForm();
    checkPasswordStrength();
  }, [formData]);

  const checkPasswordStrength = () => {
    const { password } = formData;
    const reqs = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password)
    };

    const score = Object.values(reqs).filter(Boolean).length;
    setPasswordStrength({ score, requirements: reqs });
  };

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

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setValidationErrors(errors);
    setIsValid(Object.keys(errors).length === 0 && passwordStrength.score >= 3);

  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) return;
    await register(formData.email.trim(), formData.password.trim());
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
        <label htmlFor="register-email" className="text-sm text-gray-400">
          Email
        </label>
        <input
          type="email"
          id="register-email"
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
        <label htmlFor="register-password" className="text-sm text-gray-400">
          Password
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            id="register-password"
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
            aria-describedby="password-requirements"
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
          <span className="text-sm text-red-500 mt-1">
            {validationErrors.password}
          </span>
        )}
        <div id="password-requirements" className="mt-2 space-y-1">
          <div className="text-sm text-gray-400">Password requirements:</div>
          <ul className="space-y-1">
            {Object.entries(passwordStrength.requirements).map(([key, met]) => (
              <li key={key} className="flex items-center gap-2 text-sm">
                {met ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <X className="h-4 w-4 text-red-500" />
                )}
                <span className={met ? 'text-green-500' : 'text-red-500'}>
                  {key === 'length' ? 'At least 8 characters' :
                   key === 'uppercase' ? 'One uppercase letter' :
                   key === 'lowercase' ? 'One lowercase letter' :
                   key === 'number' ? 'One number' :
                   'One special character'}
                </span>
              </li>
            ))}
          </ul>
          <div className="flex gap-1 mt-2">
            {[1, 2, 3, 4, 5].map((score) => (
              <div
                key={score}
                className={`h-2 flex-1 rounded-full transition-colors duration-200 ${
                  score <= passwordStrength.score
                    ? score <= 2
                      ? 'bg-red-500'
                      : score <= 3
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                    : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="confirm-password" className="text-sm text-gray-400">
          Confirm Password
        </label>
        <div className="relative">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirm-password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            className={cn(
              "w-full px-3 py-2 bg-gray-800 border rounded-md text-sm",
              "text-gray-200 placeholder-gray-500",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50",
              "transition-colors duration-200 pr-10",
              "border-gray-600",
              "focus:border-blue-500/50",
              "has-[:focus]:border-blue-500/50",
              validationErrors.confirmPassword && formData.confirmPassword && "border-red-500"
            )}
            aria-invalid={!!validationErrors.confirmPassword}
            aria-describedby={validationErrors.confirmPassword ? 'confirm-password-error' : undefined}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 focus:outline-none"
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {validationErrors.confirmPassword && (
          <span id="confirm-password-error" className="text-sm text-red-500 mt-1">
            {validationErrors.confirmPassword}
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
        {isAuthenticating ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}