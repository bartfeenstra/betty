/// <reference types="cypress" />

const childProcess = require('child_process')
const fs = require('fs')
const path = require('path')

/**
 * @type {Cypress.PluginConfig}
 */
module.exports = (on, config) => {
  on('task', {
    generate (args) {
      const [bettyConfiguration, gramps] = args
      const siteDirectoryPath = path.join(config.fileServerFolder, 'cypress', 'site')
      fs.mkdirSync(siteDirectoryPath, {
        recursive: true
      })
      bettyConfiguration.output = path.join(siteDirectoryPath, 'output')
      // We do not know the real base URL, but as Betty requires one, set an obviously fake value.
      bettyConfiguration.base_url = 'https://example.com'
      const rootPath = '/cypress/site/output/www'
      bettyConfiguration.root_path = rootPath
      if (!('plugins' in bettyConfiguration)) {
        bettyConfiguration.plugins = {}
      }
      bettyConfiguration.plugins['betty.plugin.gramps.Gramps'] = {
        file: path.join(siteDirectoryPath, 'gramps.xml')
      }
      fs.writeFileSync(path.join(siteDirectoryPath, 'betty.json'), JSON.stringify(bettyConfiguration))
      fs.writeFileSync(path.join(siteDirectoryPath, 'gramps.xml'), gramps)
      childProcess.execSync('betty generate', {
        cwd: siteDirectoryPath
      })
      return rootPath
    }
  })
}
