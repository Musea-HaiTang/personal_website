/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        paper: { DEFAULT: '#f7f5f1', soft: '#f4f1ea' },
        card: '#fffefc',
        hairline: '#e9e3d9',
        ink: '#2b2622',
        sub: '#7c7468',
        teal: { DEFAULT: '#0e7c74', dark: '#0a6a63', soft: '#e7f1ef' },
        plum: '#7c5cbf',
        blue: '#3b6fd4',
        green: { DEFAULT: '#3d9970', soft: '#e7f1ec' },
        amber: { DEFAULT: '#b7791f', dark: '#9a641a', soft: '#faf1dd' },
        red: { DEFAULT: '#c4533a', soft: '#f9ebe5' }
      },
      fontFamily: {
        serif: ['"Songti SC"', '"STSong"', 'SimSun', 'serif']
      }
    }
  },
  plugins: []
}
