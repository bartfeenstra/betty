'use strict'

import { test as base } from '@playwright/test'
import { access, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { createServer, IncomingMessage, Server as HttpServer, ServerResponse } from 'node:http'
import * as path from 'node:path'
import { tmpdir } from 'node:os'
import { exec as childProcessExec } from 'node:child_process'
import { createReadStream, ReadStream } from 'node:fs'

async function sleep (milliseconds: number): Promise<unknown> {
  return new Promise(resolve => setTimeout(resolve, milliseconds))
}

function exec (command: string, options: object): Promise<string | Buffer> {
  return new Promise((resolve, reject) => {
    childProcessExec(command, options, (error, stdout) => {
      if (error === null) {
        resolve(stdout)
      } else {
        reject(error)
      }
    })
  })
}

interface ServerResponseMeta {
  contentType: string
  content: ReadStream
  code: number
}

class Server implements Disposable {
  private attemptedPortNumber = 8000
  private readonly contentTypes: Record<string, string> = {
    default: 'application/octet-stream',
    html: 'text/html; charset=UTF-8',
    js: 'application/javascript',
    css: 'text/css',
    png: 'image/png',
    jpg: 'image/jpg',
    gif: 'image/gif',
    ico: 'image/x-icon',
    svg: 'image/svg+xml'
  }

  private readonly host = '127.0.0.1'
  private readonly httpServer: HttpServer
  private portNumber: number | null = null
  private readonly wwwDirectoryPath: string

  public constructor (wwwDirectoryPath: string) {
    this.wwwDirectoryPath = wwwDirectoryPath

    this.httpServer = createServer(
      (request: IncomingMessage, response: ServerResponse) => {
        void (async () :Promise<void> => {
          const responseMeta = await this.prepareFile(request.url)
          response.writeHead(
            responseMeta.code,
            {
              'Content-Type': responseMeta.contentType
            }
          )
          responseMeta.content.pipe(response)
        })()
      }
    )
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

  private async prepareFile (urlPath: string): Promise<ServerResponseMeta> {
    const urlPathComponents = [this.wwwDirectoryPath, urlPath]
    if (urlPath.endsWith('/')) {
      urlPathComponents.push('index.html')
    }
    const requestFilePath = path.join(...urlPathComponents)
    let requestFileFound: boolean
    try {
      await access(requestFilePath)
      requestFileFound = true
    } catch {
      requestFileFound = false
    }
    const responseStreamPath = requestFileFound ? requestFilePath : this.wwwDirectoryPath + '/.error/404.html'
    const fileExtension = path.extname(responseStreamPath).substring(1).toLowerCase()
    return {
      code: requestFileFound ? 200 : 404,
      content: createReadStream(responseStreamPath),
      contentType: this.contentTypes[fileExtension] || this.contentTypes.default
    }
  }

  public async getPublicUrl (): Promise<string> {
    while (this.portNumber === null) {
      await sleep(10)
    }
    return `http://${this.host}:${this.portNumber.toString()}`
  }

  private listen (): void {
    this.httpServer.listen(
      ++this.attemptedPortNumber,
      this.host,
      () => {
        this.portNumber = this.attemptedPortNumber
      }
    )
  }

  public close (): void {
    this.httpServer.close()
  }

  public [Symbol.dispose] (): void {
    this.close()
  }
}

const test = base.extend<{
  generateSite: (projectDirectoryPath: string, bettyConfiguration: object) => Promise<void>,
  temporaryDirectoryPath: string,
}>({
  generateSite: async ({temporaryDirectoryPath}, use) => {
    await use(async (projectDirectoryPath: string, bettyConfiguration: object): Promise<void> => {
      await writeFile(path.join(projectDirectoryPath, 'betty.json'), JSON.stringify(bettyConfiguration))
      await exec('betty generate', {
        cwd: projectDirectoryPath,
        env: {
          ...process.env,
          'BETTY_CACHE_DIRECTORY': temporaryDirectoryPath,
        },
      })
    })
  },
  temporaryDirectoryPath: async (
    {}, // eslint-disable-line no-empty-pattern
    use
  ) => {
    const temporaryDirectoryPath = await mkdtemp(path.join(tmpdir(), 'betty-playwright-'))
    await use(temporaryDirectoryPath)
    await rm(temporaryDirectoryPath, {
      force: true,
      recursive: true
    })
  }
})

export {
  Server,
  test
}
