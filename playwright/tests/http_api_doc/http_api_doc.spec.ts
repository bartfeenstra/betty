import * as path from 'node:path'
import { buildApp, Server, test as base } from '../index'
import { expect } from '@playwright/test'

const test = base.extend<{
  site: string,
}>({
  site: async ({ temporaryDirectoryPath }, use) => {
    using server = new Server(path.join(temporaryDirectoryPath, 'output', 'www'))
    await buildApp(temporaryDirectoryPath, {
      base_url: await server.getPublicUrl(),
      extensions: {
        'betty.extension.HttpApiDoc': {}
      }
    })
    await use(await server.getPublicUrl())
  }
})

test('load the HTTP API documentation', async ({ page, site }) => {
  await page.goto(site + '/api/index.html')
  expect(await page.content()).toContain('Betty')
})
