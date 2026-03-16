"use strict"

import "./main.scss"
import { BETTY } from "@betty.py/betty/main.ts"
import { initializeFullScreenControls } from "@betty.py/betty/full-screen.ts"
import { initializeMaps, MapOptions } from "./map.ts"
// @ts-expect-error: options.json is generated dynamically.
import optionsJson from "./options.json"
import { getLocale } from "@betty.py/betty/locale/index.ts"

await BETTY.addInitializer(initializeFullScreenControls)
const mapOptions = JSON.parse(optionsJson as string) as MapOptions
await BETTY.addInitializer(async (element: HTMLElement) => {
    await initializeMaps(element, mapOptions, getLocale())
})
