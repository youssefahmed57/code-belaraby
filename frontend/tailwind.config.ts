import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070B15",
          900: "#0B1120",
          800: "#131C31",
          700: "#1E2942",
        },
        brand: {
          blue: "#3B82F6",
          blueHover: "#2563EB",
          red: "#EF4444",
          redHover: "#DC2626",
          gold: "#F59E0B"
        }
      },
      fontFamily: {
        cairo: ["Cairo", "sans-serif"]
      }
    },
  },
  plugins: [],
};
export default config;
