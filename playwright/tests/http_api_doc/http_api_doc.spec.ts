import * as path from 'node:path'
import { Server, test as base } from '../index'
import { expect } from '@playwright/test'

const test = base.extend<{
  site: string,
}>({
  site: async ({ generateSite, temporaryDirectoryPath }, use) => {
    using server = new Server(path.join(temporaryDirectoryPath, 'output', 'www'))
    await generateSite(temporaryDirectoryPath, {
      url: await server.getPublicUrl(),
      extensions: {
        'http-api-doc': {}
      }
    })
    await use(await server.getPublicUrl())
  }
})

test('load the HTTP API documentation', async ({ page, site }) => {
  await page.goto(site + '/api/index.html')
  const content = await page.content()
  // Test a couple of keywords in the source.
  expect(content).toContain('Betty')
  expect(content).toContain('api/index.json')
  // Test a couple of keywords shown after successful rendering.
  expect(content).toContain('Retrieve a single')
  expect(content).toContain('Retrieve the collection')
  await page.close()
})
