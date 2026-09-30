/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        surfaceHover: '#334155',
        primary: '#3b82f6',
        primaryHover: '#2563eb',
        text: '#f8fafc',
        textMuted: '#94a3b8',
        border: '#334155',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        critical: '#b91c1c',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
