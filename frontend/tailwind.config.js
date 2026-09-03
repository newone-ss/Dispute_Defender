/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0369a1',
          700: '#072654',
          800: '#0c1b33',
          900: '#070d18',
        },
        razorpay: {
          blue: '#528ff0',
          dark: '#072654',
          surface: '#0a0e1a',
          card: '#111827',
          border: '#1e293b',
        }
      }
    },
  },
  plugins: [],
}
