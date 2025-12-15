/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: '#0f172a', // Slate 900
                surface: '#1e293b',    // Slate 800
                primary: '#3b82f6',    // Blue 500
                'primary-glow': '#60a5fa', // Blue 400
                secondary: '#10b981',  // Emerald 500
                accent: '#8b5cf6',     // Violet 500
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px #3b82f6, 0 0 10px #3b82f6' },
                    '100%': { boxShadow: '0 0 20px #3b82f6, 0 0 30px #3b82f6' },
                }
            }
        },
    },
    plugins: [],
}
