/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './components/**/*.{js,jsx,ts,tsx}',
    './stories/**/*.{js,jsx,ts,tsx}',
    './renderers/**/*.{js,jsx,ts,tsx}',
    './api/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: 'class', // Use class strategy based on .dark class on html/body
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border) / <alpha-value>)',
        input: 'hsl(var(--input) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar) / <alpha-value>)',
          foreground: 'hsl(var(--sidebar-foreground) / <alpha-value>)',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          foreground: 'hsl(var(--primary-foreground) / <alpha-value>)',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary) / <alpha-value>)',
          foreground: 'hsl(var(--secondary-foreground) / <alpha-value>)',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive) / <alpha-value>)',
          foreground: 'hsl(var(--destructive-foreground) / <alpha-value>)',
        },
        success: {
          DEFAULT: 'hsl(var(--success) / <alpha-value>)',
          foreground: 'hsl(var(--success-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted) / <alpha-value>)',
          foreground: 'hsl(var(--muted-foreground) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent) / <alpha-value>)',
          foreground: 'hsl(var(--accent-foreground) / <alpha-value>)',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover) / <alpha-value>)',
          foreground: 'hsl(var(--popover-foreground) / <alpha-value>)',
        },
        card: {
          DEFAULT: 'hsl(var(--card) / <alpha-value>)',
          foreground: 'hsl(var(--card-foreground) / <alpha-value>)',
        },
        selected: {
          DEFAULT: 'hsl(var(--selected) / <alpha-value>)',
          foreground: 'hsl(var(--selected-foreground) / <alpha-value>)',
        },
        // Task status colors
        'status-todo': {
          DEFAULT: 'hsl(var(--status-todo) / <alpha-value>)',
          foreground: 'hsl(var(--status-todo-foreground) / <alpha-value>)',
        },
        'status-in-progress': {
          DEFAULT: 'hsl(var(--status-in-progress) / <alpha-value>)',
          foreground: 'hsl(var(--status-in-progress-foreground) / <alpha-value>)',
        },
        'status-done': {
          DEFAULT: 'hsl(var(--status-done) / <alpha-value>)',
          foreground: 'hsl(var(--status-done-foreground) / <alpha-value>)',
        },
        diffgreen: {
          DEFAULT: 'hsl(var(--diffgreen) / <alpha-value>)',
          foreground: 'hsl(var(--diffgreen-foreground) / <alpha-value>)',
        },
        diffred: {
          DEFAULT: 'hsl(var(--diffred) / <alpha-value>)',
          foreground: 'hsl(var(--diffred-foreground) / <alpha-value>)',
        },
        appbackground: {
          DEFAULT: 'hsl(var(--appbackground) / <alpha-value>)',
          foreground: 'hsl(var(--appbackground-foreground) / <alpha-value>)',
        },
        appbackgroundgradient1: {
          DEFAULT: 'hsl(var(--appbackgroundgradient1) / <alpha-value>)',
          foreground: 'hsl(var(--appbackgroundgradient1-foreground) / <alpha-value>)',
        },
        appbackgroundgradient2: {
          DEFAULT: 'hsl(var(--appbackgroundgradient2) / <alpha-value>)',
          foreground: 'hsl(var(--appbackgroundgradient2-foreground) / <alpha-value>)',
        },
        appbackgroundgradient3: {
          DEFAULT: 'hsl(var(--appbackgroundgradient3) / <alpha-value>)',
          foreground: 'hsl(var(--appbackgroundgradient3-foreground) / <alpha-value>)',
        },
        approve: {
          DEFAULT: 'hsl(var(--approve) / <alpha-value>)',
          foreground: 'hsl(var(--approve-foreground) / <alpha-value>)',
        },
        reject: {
          DEFAULT: 'hsl(var(--reject) / <alpha-value>)',
          foreground: 'hsl(var(--reject-foreground) / <alpha-value>)',
        },
        'action-create': {
          DEFAULT: 'hsl(var(--action-create) / <alpha-value>)',
          foreground: 'hsl(var(--action-create-foreground) / <alpha-value>)',
        },
        'action-update': {
          DEFAULT: 'hsl(var(--action-update) / <alpha-value>)',
          foreground: 'hsl(var(--action-update-foreground) / <alpha-value>)',
        },
        'action-delete': {
          DEFAULT: 'hsl(var(--action-delete) / <alpha-value>)',
          foreground: 'hsl(var(--action-delete-foreground) / <alpha-value>)',
        },
      },
      borderRadius: {
        lg: 'var(--radius-lg)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        DEFAULT: 'var(--radius)', // Overrides Tailwind's default 'rounded'
      },
      fontSize: {
        sm: 'var(--font-sm)',
        base: 'var(--font-base)',
        lg: 'var(--font-lg)',
      },
      // Add animation for gradient
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'pulse-slow': {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        'float-slow': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-15px)' },
        },
        'drift-slow': {
          '0%': { transform: 'translateX(-10px)' },
          '50%': { transform: 'translateX(10px)' },
          '100%': { transform: 'translateX(-10px)' },
        },
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-200%)' },
        },
      },
      animation: {
        'gradient': 'gradient 15s ease infinite',
        'pulse-slow': 'pulse-slow 8s ease-in-out infinite',
        'float-slow': 'float-slow 10s ease-in-out infinite',
        'drift-slow': 'drift-slow 12s ease-in-out infinite',
        'marquee': 'marquee 6s linear infinite',
      },
      // You can extend other theme sections like spacing here
      // using values from variables.scss if needed.
    },
  },
  plugins: [
    require('tailwindcss-animate'), // Added for potential future use with animations
    require('tailwind-scrollbar-hide'),
  ], 
  variants: {
    extend: {
      display: ["group-hover"],
      animation: ['hover', 'focus'],
    },
  },
};
