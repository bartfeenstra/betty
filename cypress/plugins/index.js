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
      const appDirectoryPath = path.join(config.fileServerFolder, 'cypress', 'app')
      fs.mkdirSync(appDirectoryPath, {
        recursive: true
      })
      // We do not know the real base URL, but as Betty requires one, set an obviously fake value.
      bettyConfiguration.base_url = 'https://example.com'
      const rootPath = '/cypress/app/output/www'
      bettyConfiguration.root_path = rootPath
      if (!('extensions' in bettyConfiguration)) {
        bettyConfiguration.extensions = {}
      }
      bettyConfiguration.extensions['betty.gramps.Gramps'] = {
        enabled: true,
        configuration: {
          family_trees: [
            {
              file: path.join(appDirectoryPath, 'gramps.xml')
            }
          ]
        }
      }
      fs.writeFileSync(path.join(appDirectoryPath, 'betty.json'), JSON.stringify(bettyConfiguration))
      fs.writeFileSync(path.join(appDirectoryPath, 'gramps.xml'), gramps)
      childProcess.execSync('betty generate', {
        cwd: appDirectoryPath
      })
      return rootPath
    }
  })
}
