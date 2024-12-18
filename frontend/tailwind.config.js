/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1B2541",
        secondary: "#3B82F6",
        background: "#1B2541",
        foreground: "#FFFFFF",
      },
      borderColor: {
        DEFAULT: "#3B82F6",
      },
    },
  },
  plugins: [],
}
