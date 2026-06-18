/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#0A1628',
        'steel-blue': '#1E3A5F',
        amber: '#F59E0B',
        'alert-red': '#DC2626',
        'safe-green': '#16A34A',
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        mono: ['Roboto Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
