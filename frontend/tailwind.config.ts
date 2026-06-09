import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#FAF4E8",
        ivory: "#FFFDF7",
        brand: {
          DEFAULT: "#C86B3C",
          dark: "#A8552F",
          light: "#F5E6DC",
        },
        sage: {
          DEFAULT: "#6B8F71",
          light: "#E8F0E9",
        },
        espresso: "#2F2A24",
        muted: "#7A7065",
        border: {
          DEFAULT: "#E7D8C9",
          dark: "#D4C4B5",
        },
        warning: {
          DEFAULT: "#B45309",
          light: "#FEF3C7",
          border: "#FCD34D",
        },
        danger: {
          DEFAULT: "#B91C1C",
          light: "#FEE2E2",
          border: "#FECACA",
        },
        success: {
          DEFAULT: "#6B8F71",
          light: "#E8F0E9",
          border: "#A7C4AB",
        },
      },
      boxShadow: {
        soft: "0 1px 3px rgba(47, 42, 36, 0.06), 0 4px 12px rgba(47, 42, 36, 0.04)",
        card: "0 2px 8px rgba(47, 42, 36, 0.07), 0 1px 2px rgba(47, 42, 36, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
