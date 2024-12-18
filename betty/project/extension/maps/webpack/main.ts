'use strict'

import { initializeMaps } from './maps.js'

async function main(): Promise<void> {
    await initializeMaps()  // eslint-disable-line @typescript-eslint/no-unsafe-call
}
void main()
