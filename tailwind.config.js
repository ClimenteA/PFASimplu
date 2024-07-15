/** @type {import('tailwindcss').Config} */
export default {
  content: ["./components/**/*.tsx", "./pages/**/*.tsx", "*.tsx"],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
}

