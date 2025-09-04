/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for the dark theme
        'dark-bg': '#1a1a1a',
        'dark-card': '#2a2a2a',
        'dark-border': '#404040',
        'orange-accent': '#ff8c42',
        'orange-hover': '#ff7a2b',
      },
    },
  },
  plugins: [],
}
