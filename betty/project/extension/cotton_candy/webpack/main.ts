"use strict"

import { initializeFiles } from "./file.ts"
import { Search } from "./search.ts"
import { initializeToggles } from "./show.ts"
import "./main.scss"
import { BETTY } from "@betty.py/betty/main.ts"
import { initializeFullScreenControls } from "@betty.py/betty/full-screen.ts"

await BETTY.addInitializer(initializeFullScreenControls)

async function main(): Promise<void> {
    await Promise.allSettled([
        initializeFiles(),
        initializeToggles(),
    ])
    const search = new Search()
    search.initialize()
}

void main()
