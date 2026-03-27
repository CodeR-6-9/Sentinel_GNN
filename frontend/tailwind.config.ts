import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#020617",
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-in-out",
        "slide-in-from-left": "slide-in-from-left 0.4s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;