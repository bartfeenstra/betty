import * as path from 'node:path'
import { buildApp, Server, test as base } from '../index'
import { expect } from '@playwright/test'

const test = base.extend<{
  site: string,
}>({
  site: async ({ temporaryDirectoryPath }, use) => {
    const projectDirectoryPath = await buildApp(temporaryDirectoryPath, {
      extensions: {
        'betty.extension.HttpApiDoc': {}
      }
    })
    using server = new Server(path.join(projectDirectoryPath, 'output', 'www'))
    await use(await server.getPublicUrl())
  }
})

test('load the HTTP API documentation', async ({ page, site }) => {
  await page.goto(site + '/api/index.html')
  expect(await page.content()).toContain('Betty')
})
