/** Tailwind build for Django templates (dev static bundle). */
module.exports = {
  content: [
    "./src/pylucy/templates/**/*.html",
    "./src/**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
