import { test as base } from '@playwright/test'
import { mkdtemp, writeFile } from 'node:fs/promises'
import * as path from 'node:path'
import { tmpdir } from 'node:os'
import { createServer, Server as HttpServer } from 'node:http'
import serveStatic = require('serve-static');
import connect = require('connect');
import { exec as childProcessExec } from 'node:child_process'

async function sleep (milliseconds: number): Promise<unknown> {
  return new Promise(resolve => setTimeout(resolve, milliseconds))
}

function exec (command: string, options: object): Promise<string | Buffer> {
  return new Promise((resolve, reject) => {
    childProcessExec(command, options, (error, stdout, stderr) => {
      if (error === null) {
        resolve(stdout)
      } else {
        reject(stderr)
      }
    })
  })
}

async function buildApp (projectDirectoryPath: string, bettyConfiguration: object): Promise<string> {
  // We do not know the real base URL, but as Betty requires one, set an obviously fake value.
  bettyConfiguration.base_url = 'https://example.com'
  await writeFile(path.join(projectDirectoryPath, 'betty.json'), JSON.stringify(bettyConfiguration))
  await exec('betty generate', {
    cwd: projectDirectoryPath
  })
  return projectDirectoryPath
}

class Server implements Disposable {
  private readonly host = '127.0.0.1'
  private httpServer: HttpServer
  private portNumber: number | null = null
  private attemptedPortNumber = 8000

  constructor (wwwDirectoryPath: string) {
    const app = connect()
      .use(serveStatic(wwwDirectoryPath))
    this.httpServer = createServer(app)
    this.httpServer.on('error', (error) => {
      if (error.code === 'EADDRINUSE') {
        this.httpServer.close()
        this.listen()
        return
      }
      throw error
    })
    this.listen()
  }

  private listen (): void {
    this.httpServer.listen(++this.attemptedPortNumber, this.host, () => {
      this.portNumber = this.attemptedPortNumber
    })
  }

  public async getPublicUrl (): Promise<string> {
    while (this.portNumber === null) {
      await sleep(10)
    }
    return `http://${this.host}:${this.portNumber}`
  }

  public async [Symbol.dispose] () {
    this.httpServer.close()
  }
}

const test = base.extend<{
  temporaryDirectoryPath: string,
}>({
  temporaryDirectoryPath: async (
    {}, // eslint-disable-line no-empty-pattern
    use
  ) => {
    await use(await mkdtemp(path.join(tmpdir(), 'betty-playwright-')))
  }
})

module.exports = {
  buildApp,
  Server,
  test
}
