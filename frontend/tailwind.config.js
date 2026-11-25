/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          900: '#070b13',
          850: '#0b111e',
          800: '#0f172a',
          750: '#15203b',
          700: '#1e293b',
          border: 'rgba(56, 189, 248, 0.15)',
        },
        neon: {
          cyan: '#00f0ff',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          purple: '#a855f7',
          blue: '#3b82f6',
        }
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(0, 240, 255, 0.4)',
        'glow-rose': '0 0 20px -3px rgba(244, 63, 94, 0.4)',
        'glow-emerald': '0 0 20px -3px rgba(16, 185, 129, 0.4)',
        'glow-amber': '0 0 20px -3px rgba(245, 158, 11, 0.4)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-scan': 'scan 8s linear infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      }
    },
  },
  plugins: [],
}
