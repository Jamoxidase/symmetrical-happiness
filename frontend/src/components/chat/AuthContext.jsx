import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

const AuthContext = createContext(null);
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Storage keys for persistent auth state
const ACCESS_TOKEN_KEY = 'chat_access_token';
const REFRESH_TOKEN_KEY = 'chat_refresh_token';
const USER_STORAGE_KEY = 'chat_user';

// Constants for token refresh
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes in milliseconds
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY = 1000; // 1 second

// Helper to extract tokens from response
const extractTokens = (data) => {
  return {
    accessToken: data.access_token || data.token || null,
    refreshToken: data.refresh_token || null
  };
};

// Helper to decode JWT token
const decodeToken = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      ...payload,
      expiresAt: payload.exp * 1000 // Convert to milliseconds
    };
  } catch (err) {
    console.error('Error decoding token:', err);
    return null;
  }
};

// Helper to check if a token is about to expire
const isTokenExpiringSoon = (token) => {
  const decoded = decodeToken(token);
  if (!decoded) return true;
  return Date.now() + TOKEN_REFRESH_THRESHOLD >= decoded.expiresAt;
};

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(() => {
    // Try to restore auth state from storage
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const userStr = localStorage.getItem(USER_STORAGE_KEY);
    
    let user = null;
    try {
      user = userStr ? JSON.parse(userStr) : null;
    } catch (err) {
      console.error('Error parsing stored user data:', err);
    }

    // Validate stored tokens
    if (accessToken && refreshToken && user) {
      const decoded = decodeToken(accessToken);
      if (decoded && decoded.expiresAt > Date.now()) {
        return {
          isAuthenticated: true,
          accessToken,
          refreshToken,
          user,
          error: null,
          isAuthenticating: false,
          lastTokenRefresh: Date.now()
        };
      }
    }

    // Clear invalid stored data
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);

    return {
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
      user: null,
      error: null,
      isAuthenticating: false,
      lastTokenRefresh: null
    };
  });

  // Ref for tracking refresh token promise
  const refreshTokenPromise = useRef(null);

  const setAuthData = useCallback(({ accessToken, refreshToken, user }) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    
    setAuthState({
      isAuthenticated: true,
      accessToken,
      refreshToken,
      user,
      error: null,
      isAuthenticating: false,
      lastTokenRefresh: Date.now()
    });
  }, []);

  const clearAuthData = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    
    setAuthState({
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
      user: null,
      error: null,
      isAuthenticating: false,
      lastTokenRefresh: null
    });
  }, []);

  // Refresh token with smarter error handling
  const refreshTokens = useCallback(async () => {
    // Return existing promise if refresh is in progress
    if (refreshTokenPromise.current) {
      return refreshTokenPromise.current;
    }

    const refreshAttempt = async () => {
      try {
        const response = await fetch(`${API_URL}/auth/refresh/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            refresh_token: authState.refreshToken
          })
        });

        // Handle specific error cases
        if (response.status === 401 || response.status === 403) {
          // Token is invalid or expired - no point retrying
          clearAuthData();
          throw new Error('Session expired. Please log in again.');
        }

        if (!response.ok) {
          // Only retry on network errors or 5xx server errors
          const isServerError = response.status >= 500 && response.status < 600;
          if (!isServerError) {
            clearAuthData();
            throw new Error('Authentication failed. Please log in again.');
          }
          throw new Error('Token refresh failed');
        }

        const data = await response.json();
        const { accessToken, refreshToken } = extractTokens(data);
        
        if (!accessToken || !refreshToken) {
          clearAuthData();
          throw new Error('Invalid token response from server. Please log in again.');
        }

        setAuthData({
          accessToken,
          refreshToken,
          user: authState.user
        });

        return accessToken;
      } catch (error) {
        // If error indicates auth failure, don't retry
        if (error.message.includes('Please log in again')) {
          throw error;
        }
        
        // Only retry on network errors or server errors
        if (error.message === 'Token refresh failed') {
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          return refreshAttempt();
        }
        
        throw error;
      }
    };

    try {
      refreshTokenPromise.current = refreshAttempt();
      const result = await refreshTokenPromise.current;
      return result;
    } finally {
      refreshTokenPromise.current = null;
    }
  }, [authState.refreshToken, authState.user, setAuthData, clearAuthData]);

  const handleAuthError = useCallback((error) => {
    console.error('Auth error:', error);
    const errorMessage = error.message || 'Authentication failed';
    
    // Clear auth data on critical errors
    if (error.message?.includes('Token') || error.message?.includes('Authentication')) {
      clearAuthData();
    } else {
      setAuthState(prev => ({
        ...prev,
        error: errorMessage,
        isAuthenticating: false
      }));
    }
  }, [clearAuthData]);

  const login = useCallback(async (email, password) => {
    setAuthState(prev => ({ ...prev, isAuthenticating: true, error: null }));

    try {
      const response = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMsg = errorData.error === 'Invalid credentials' 
          ? 'Incorrect email or password'
          : errorData.error || 'Unable to log in. Please try again.';
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const { accessToken, refreshToken } = extractTokens(data);
      
      if (!accessToken || !refreshToken) {
        throw new Error('Invalid token response from server');
      }

      setAuthData({
        accessToken,
        refreshToken,
        user: data.user
      });

      return true;
    } catch (err) {
      handleAuthError(err);
      return false;
    }
  }, [setAuthData, handleAuthError]);

  const register = useCallback(async (email, password) => {
    setAuthState(prev => ({ ...prev, isAuthenticating: true, error: null }));

    try {
      const response = await fetch(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMsg = errorData.error === 'Email already exists' 
          ? 'An account with this email already exists'
          : errorData.error || 'Unable to create account. Please try again.';
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const { accessToken, refreshToken } = extractTokens(data);
      
      if (!accessToken || !refreshToken) {
        throw new Error('Invalid token response from server');
      }

      setAuthData({
        accessToken,
        refreshToken,
        user: data.user
      });

      return true;
    } catch (err) {
      handleAuthError(err);
      return false;
    }
  }, [setAuthData, handleAuthError]);

  const logout = useCallback(() => {
    clearAuthData();
  }, [clearAuthData]);

  // Token refresh and expiration check with better error handling
  useEffect(() => {
    if (!authState.accessToken || !authState.refreshToken) return;

    let timeoutId;
    const decoded = decodeToken(authState.accessToken);
    if (!decoded) {
      // Invalid token format, clear auth
      clearAuthData();
      return;
    }

    const timeUntilExpiry = decoded.expiresAt - Date.now();
    // Schedule refresh 5 minutes before expiry
    const refreshTime = Math.max(0, timeUntilExpiry - TOKEN_REFRESH_THRESHOLD);
    
    const handleRefresh = async () => {
      try {
        await refreshTokens();
      } catch (err) {
        console.error('Token refresh failed:', err);
        // Don't reload the page, just clear auth and let the UI handle it
        clearAuthData();
        // The error from refreshTokens will already indicate need to log in again
      }
    };

    // Only attempt refresh if token is not already expired
    if (timeUntilExpiry > 0) {
      if (refreshTime === 0) {
        // Token is near expiry but still valid, refresh immediately
        handleRefresh();
      } else {
        // Schedule the refresh
        timeoutId = setTimeout(handleRefresh, refreshTime);
      }
    } else {
      // Token is already expired, clear auth
      clearAuthData();
    }

    return () => {
      clearTimeout(timeoutId);
    };
  }, [authState.accessToken, authState.refreshToken, refreshTokens, clearAuthData]);

  // Create an authenticated fetch wrapper with better error handling
  const authFetch = useCallback(async (url, options = {}) => {
    if (!authState.accessToken) {
      throw new Error('No access token available');
    }

    const makeRequest = async (token) => {
      const authOptions = {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`
        }
      };

      const response = await fetch(url, authOptions);
      
      // Handle auth errors
      if (response.status === 401) {
        try {
          // Try to refresh the token once
          const newToken = await refreshTokens();
          // Make one more attempt with the new token
          const retryResponse = await fetch(url, {
            ...authOptions,
            headers: {
              ...authOptions.headers,
              'Authorization': `Bearer ${newToken}`
            }
          });

          // If still unauthorized, we need to log in again
          if (retryResponse.status === 401) {
            clearAuthData();
            throw new Error('Your session has expired. Please log in again.');
          }

          return retryResponse;
        } catch (err) {
          // If refresh fails or second attempt fails, clear auth
          clearAuthData();
          // Propagate the error message from refreshTokens if available
          throw new Error(err.message || 'Authentication failed. Please log in again.');
        }
      }

      return response;
    };

    try {
      return await makeRequest(authState.accessToken);
    } catch (err) {
      // If it's an auth error, propagate it
      if (err.message.includes('log in again') || err.message.includes('session')) {
        throw err;
      }
      // For other errors, give a generic message
      throw new Error('Request failed. Please check your connection and try again.');
    }
  }, [authState.accessToken, refreshTokens, clearAuthData]);

  const value = {
    ...authState,
    login,
    register,
    logout,
    authFetch,
    isTokenExpiringSoon: useCallback(
      () => authState.accessToken ? isTokenExpiringSoon(authState.accessToken) : true,
      [authState.accessToken]
    )
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};