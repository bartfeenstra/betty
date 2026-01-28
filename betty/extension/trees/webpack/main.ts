"use strict"

import "./main.scss"
import { initializeAncestryTrees } from "./trees.js"

import { BETTY } from "@betty.py/betty/main.ts"
// @ts-expect-error: options.json is generated dynamically.
import optionsJson from "./options.json"
import { TreeOptions } from "@betty.py/betty.extension.trees/tree"

const treeOptions = JSON.parse(optionsJson as string) as TreeOptions
await BETTY.addInitializer(async (element: HTMLElement) => {
    await initializeAncestryTrees(element, treeOptions) // eslint-disable-line @typescript-eslint/no-unsafe-call
})
