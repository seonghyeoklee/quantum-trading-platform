import tailwindcssAnimate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--background))",
        foreground: "rgb(var(--foreground))",
        card: {
          DEFAULT: "rgb(var(--card))",
          foreground: "rgb(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "rgb(var(--popover))",
          foreground: "rgb(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "rgb(var(--primary))",
          foreground: "rgb(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "rgb(var(--secondary))",
          foreground: "rgb(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "rgb(var(--muted))",
          foreground: "rgb(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "rgb(var(--accent))",
          foreground: "rgb(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "rgb(var(--destructive))",
          foreground: "rgb(var(--destructive-foreground))",
        },
        border: "rgb(var(--border))",
        input: "rgb(var(--input))",
        ring: "rgb(var(--ring))",
        chart: {
          "1": "rgb(var(--chart-1))",
          "2": "rgb(var(--chart-2))",
          "3": "rgb(var(--chart-3))",
          "4": "rgb(var(--chart-4))",
          "5": "rgb(var(--chart-5))",
          "6": "rgb(var(--chart-6))",
          "7": "rgb(var(--chart-7))",
          "8": "rgb(var(--chart-8))",
        },
        sidebar: {
          DEFAULT: "rgb(var(--sidebar))",
          foreground: "rgb(var(--sidebar-foreground))",
          primary: "rgb(var(--sidebar-primary))",
          "primary-foreground": "rgb(var(--sidebar-primary-foreground))",
          accent: "rgb(var(--sidebar-accent))",
          "accent-foreground": "rgb(var(--sidebar-accent-foreground))",
          border: "rgb(var(--sidebar-border))",
          ring: "rgb(var(--sidebar-ring))",
        },
        // Professional Financial Trading Colors
        bull: "rgb(var(--bull-green))",
        bear: "rgb(var(--bear-red))", 
        "bull-green": "rgb(var(--bull-green))",
        "bear-red": "rgb(var(--bear-red))",
        "warning-amber": "rgb(var(--warning-amber))",
        "info-blue": "rgb(var(--info-blue))",
        "success-emerald": "rgb(var(--success-emerald))",
        // Extended Professional Chart Colors
        "chart-1": "rgb(var(--chart-1))",
        "chart-2": "rgb(var(--chart-2))",
        "chart-3": "rgb(var(--chart-3))",
        "chart-4": "rgb(var(--chart-4))",
        "chart-5": "rgb(var(--chart-5))",
        "chart-6": "rgb(var(--chart-6))",
        "chart-7": "rgb(var(--chart-7))",
        "chart-8": "rgb(var(--chart-8))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)"],
        mono: ["var(--font-geist-mono)"],
      },
    },
  },
  plugins: [tailwindcssAnimate],
};