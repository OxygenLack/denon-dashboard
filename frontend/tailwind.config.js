/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        denon: {
          gold: '#C5A55A',
          dark: '#0D0D0D',
          card: '#1A1A1A',
          surface: '#242424',
          border: '#333333',
          text: '#E5E5E5',
          muted: '#888888',
          accent: '#C5A55A',
          green: '#4ADE80',
          red: '#EF4444',
          blue: '#60A5FA',
        },
      },
    },
  },
  plugins: [],
}
