import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "oklch(0.145 0 0)",
        foreground: "oklch(0.985 0 0)",
        card: {
          DEFAULT: "oklch(0.145 0 0)",
          foreground: "oklch(0.985 0 0)",
        },
        popover: {
          DEFAULT: "oklch(0.145 0 0)",
          foreground: "oklch(0.985 0 0)",
        },
        primary: {
          DEFAULT: "oklch(0.985 0 0)",
          foreground: "oklch(0.205 0 0)",
        },
        secondary: {
          DEFAULT: "oklch(0.269 0 0)",
          foreground: "oklch(0.985 0 0)",
        },
        muted: {
          DEFAULT: "oklch(0.269 0 0)",
          foreground: "oklch(0.708 0 0)",
        },
        accent: {
          DEFAULT: "oklch(0.269 0 0)",
          foreground: "oklch(0.985 0 0)",
        },
        destructive: {
          DEFAULT: "oklch(0.396 0.141 25.723)",
          foreground: "oklch(0.637 0.237 25.331)",
        },
        border: "oklch(0.269 0 0)",
        input: "oklch(0.269 0 0)",
        ring: "oklch(0.556 0 0)",
      },
      borderRadius: {
        lg: "0.625rem",
        md: "calc(0.625rem - 2px)",
        sm: "calc(0.625rem - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
