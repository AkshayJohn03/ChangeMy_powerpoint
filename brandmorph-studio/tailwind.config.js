/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    screens: {
      mobile: '390px',
      tablet: '768px',
      desktop: '1200px',
      'wide-safe': '1800px',
    },
    extend: {
      colors: {
        'primary-blue': {
          50: '#EFF6FB',
          100: '#DCEAF6',
          200: '#B9D5EC',
          300: '#93BCE1',
          400: '#6EA1D6',
          500: '#2B74B6', // Core Primary
          600: '#0F78B0', // Hover / Deep Accent
          700: '#164A7A',
          800: '#10385C',
          900: '#0A253D', // Navy Container
          950: '#030C1E', // Canvas Dark Base
        },
        'sage-olive': {
          50: '#F5F7F4',
          100: '#E6EBE4',
          200: '#CED6CC',
          300: '#AEBBAB',
          400: '#8A9A86',
          500: '#6C7A68', // Secondary Core
          600: '#545F51',
          700: '#444D42',
          800: '#383F36', // Dark Sage
          900: '#30352E',
        },
        'warm-gold': {
          500: '#FF9900', // Warm Gold Core
        },
        'cyan-uplink': {
          500: '#029FA0', // Cyan Uplink
        },
        emerald: {
          500: '#10B981', // High Capacity / Verified
        },
        rose: {
          500: '#EF4444', // Low Capacity / Alert Red
        },
        amber: {
          500: '#F59E0B', // Medium Capacity Warning
        },
      },
      fontFamily: {
        display: ['Cabinet Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      minHeight: {
        'touch-target': '48px',
      },
      minWidth: {
        'touch-target': '48px',
      },
      zIndex: {
        dropdown: '1000',
        'sticky-header': '1100',
        modal: '1200',
        toast: '1300',
      },
      boxShadow: {
        'sm-subtle': '0 1px 2px rgba(0,0,0,0.05)',
        'md-card': '0 4px 6px -1px rgba(0,0,0,0.1)',
        'lg-elevated': '0 10px 15px -3px rgba(0,0,0,0.1)',
      },
      transitionTimingFunction: {
        'ease-out-smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};
