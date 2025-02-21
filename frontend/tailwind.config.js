/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#001F3F',
        'soft-white': '#F6F6F6',
        'gray-light': '#B0B0B0',
        coral: '#FF6F61',
        gold: '#FFD700',
        offwhite: '#FAFAFA',
        divider: '#E0E0E0',
      },
      animation: {
        "fade-in": "fade-in 0.15s ease-out",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: 0.8 },
          "100%": { opacity: 1 },
        },
      },
      fontFamily: {
        sans: ['Roboto', 'Open Sans', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'input': '18px',
        'response': '16px',
        'secondary': '14px',
      },
    },
  },
  plugins: [
    require("tailwindcss-animate")
  ],
}