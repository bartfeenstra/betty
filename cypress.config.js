const { defineConfig } = require('cypress')

module.exports = defineConfig({
  video: false,
  e2e: {
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config)
    },
  },
})
