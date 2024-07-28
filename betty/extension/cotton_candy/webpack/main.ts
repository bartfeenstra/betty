'use strict'

import { initializeFiles } from './file.ts'
import { Search } from './search.ts'
import { initializeToggles } from './show.ts'
import './main.scss'

async function main(): Promise<void> {
    await Promise.allSettled([
        initializeFiles(),
        initializeToggles(),
    ])
    const search = new Search()
    search.initialize()
}
void main()
