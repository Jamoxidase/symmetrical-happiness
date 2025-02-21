export const designSystem = {
  colors: {
    // Primary colors
    primary: {
      light: '#0A84FF',
      dark: '#0071E3',
    },
    
    // Background colors
    background: {
      body: '#0F0F0F',  // Perplexity's dark background
      surface: '#1A1A1A',  // Slightly lighter for elements
      input: '#1E1E1E',  // Input background
      hover: '#252525',  // Hover state
    },
    
    // Text colors
    text: {
      primary: '#FFFFFF',  // Pure white for better contrast
      secondary: '#999999',  // Subtle gray for secondary text
      tertiary: '#666666',  // More subtle for tertiary text
    },
    
    // Accent colors
    accent: {
      success: '#34D399',
      warning: '#F59E0B',
      error: '#EF4444',
    },
    
    // UI element colors
    ui: {
      border: '#3A3A3C',
      separator: '#2C2C2E',
      hover: '#2D2D2D',
    }
  },

  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif',
      code: '"SF Mono", Menlo, monospace',
    },
    fontSize: {
      user: '22px',
      assistant: '18px',
      input: '18px',
      ui: '14px',
    },
    lineHeight: {
      body: 1.65,
      relaxed: 1.75,
    },
    letterSpacing: {
      tight: '-0.01em',
      normal: '0.01em',
    },
  },

  spacing: {
    unit: '0.25rem',
    1: 'calc(1 * var(--space-unit))',
    2: 'calc(2 * var(--space-unit))',
    3: 'calc(3 * var(--space-unit))',
    4: 'calc(4 * var(--space-unit))',
    6: 'calc(6 * var(--space-unit))',
    8: 'calc(8 * var(--space-unit))',
  },

  layout: {
    maxWidth: '1440px',
    messageWidth: '800px',
    borderRadius: {
      sm: '6px',
      md: '8px',
      lg: '12px',
      xl: '16px',
    },
  },

  animation: {
    timing: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      default: 'cubic-bezier(0.22, 1, 0.36, 1)',
      bounce: 'cubic-bezier(0.37, 0, 0.63, 1)',
    },
  },

  shadows: {
    sm: '0 2px 4px rgba(0,0,0,0.1)',
    md: '0 4px 12px rgba(0,0,0,0.15)',
    lg: '0 8px 24px rgba(0,0,0,0.2)',
  },
};