'use strict'

import { initializeAncestryTrees } from './trees.js'

async function main(): Promise<void> {
    await initializeAncestryTrees()  // eslint-disable-line @typescript-eslint/no-unsafe-call
}
void main()
