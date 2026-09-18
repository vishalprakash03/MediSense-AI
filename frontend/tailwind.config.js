/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefbf6",
          100: "#d5f5ea",
          500: "#0f9d75",
          600: "#0c8462",
          700: "#0a6b50",
        },
      },
    },
  },
  plugins: [],
};
