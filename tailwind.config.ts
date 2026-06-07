import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#d9e6ff",
          200: "#bcd4ff",
          300: "#8eb8ff",
          400: "#5990ff",
          500: "#3366ff",
          600: "#1a44f5",
          700: "#1534e1",
          800: "#182cb6",
          900: "#192a8f",
          950: "#111a57",
        },
        slate: {
          850: "#1a2234",
          950: "#0b1120",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-plus-jakarta)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease-out forwards",
        "slide-up": "slideUp 0.6s ease-out forwards",
        "pulse-soft": "pulseSoft 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.7" },
        },
      },
      backgroundImage: {
        "enterprise-gradient":
          "linear-gradient(135deg, #0b1120 0%, #111a57 35%, #1534e1 70%, #1a44f5 100%)",
        "mesh-gradient":
          "radial-gradient(ellipse 80% 50% at 20% 40%, rgba(51, 102, 255, 0.35), transparent), radial-gradient(ellipse 60% 40% at 80% 20%, rgba(26, 68, 245, 0.25), transparent), radial-gradient(ellipse 50% 60% at 60% 80%, rgba(17, 26, 87, 0.5), transparent)",
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08)",
        "glass-lg":
          "0 24px 64px rgba(0, 0, 0, 0.16), 0 8px 24px rgba(0, 0, 0, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
