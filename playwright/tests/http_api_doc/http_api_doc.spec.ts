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
  const locator = page.locator('#swagger-ui')
  // Test a couple of keywords in the source.
  await expect(locator).toContainText('Betty')
  await expect(locator).toContainText('api/index.json')
  // Test a couple of keywords shown after successful rendering.
  await expect(locator).toContainText('Retrieve a single')
  await expect(locator).toContainText('Retrieve the collection')
  await page.close()
})
