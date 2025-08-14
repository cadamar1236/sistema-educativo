import type { Config } from 'tailwindcss'
import { nextui } from '@nextui-org/react'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        julia: {
          primary: '#6366f1',
          secondary: '#8b5cf6',
          accent: '#06b6d4',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
          dark: '#1f2937',
          light: '#f8fafc'
        }
      },
      fontFamily: {
        'julia': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'bounce-gentle': 'bounceGentle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        }
      }
    },
  },
  darkMode: "class",
  plugins: [nextui({
    addCommonColors: false,
    defaultTheme: "light",
    defaultExtendTheme: "light",
    layout: {},
    themes: {
      light: {
        layout: {},
        colors: {
          background: "#FFFFFF",
          foreground: "#11181C",
          primary: {
            50: "#eef2ff",
            100: "#e0e7ff",
            200: "#c7d2fe",
            300: "#a5b4fc",
            400: "#818cf8",
            500: "#6366f1",
            600: "#4f46e5",
            700: "#4338ca",
            800: "#3730a3",
            900: "#312e81",
            DEFAULT: "#6366f1",
            foreground: "#FFFFFF",
          },
        },
      },
      dark: {
        layout: {},
        colors: {
          background: "#0D1117",
          foreground: "#ECEDEE",
          primary: {
            50: "#1a1a2e",
            100: "#16213e",
            200: "#0f3460",
            300: "#533483",
            400: "#7209b7",
            500: "#a663cc",
            600: "#bf7dd1",
            700: "#d897d6",
            800: "#f1b1db",
            900: "#fecbe0",
            DEFAULT: "#a663cc",
            foreground: "#FFFFFF",
          },
        },
      },
    },
  })],
}
export default config
