/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B1D24",      // primary text / dark surfaces
        paper: "#F5F7F3",    // app background (faint green-tinted, not cream)
        surface: "#FFFFFF",  // cards
        line: "#E5E8E0",     // borders
        growth: "#2E9E6B",   // primary accent — the garden / growth
        sprout: "#8FD0A8",   // light green — fills / progress
        amber: "#DE9B36",    // streaks / XP / warmth
        slate: "#6B7280",    // muted text
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"Space Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: "0 1px 2px rgba(27,29,36,0.04), 0 8px 24px -12px rgba(27,29,36,0.12)",
      },
    },
  },
  plugins: [],
};
