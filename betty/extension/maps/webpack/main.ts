'use strict'

import { initializePlaceLists } from './maps.js'

async function main(): Promise<void> {
    await initializePlaceLists()  // eslint-disable-line @typescript-eslint/no-unsafe-call
}
void main()
