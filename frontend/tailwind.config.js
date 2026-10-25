/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mathrix: {
          dark: "#08090C",
          card: "#101217",
          border: "#1E222D",
          emerald: "#00FF88",
          green: "#10B981",
          amber: "#F59E0B",
          red: "#FF3366",
          text: "#E5E7EB",
          muted: "#9CA3AF"
        }
      },
      fontFamily: {
        sans: ["Inter", "Outfit", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"]
      }
    },
  },
  plugins: [],
}
