'use strict'

import './main.scss'
import {initializeAncestryTrees} from './trees.js'
import {BETTY} from "@betty.py/betty/main.ts"

await BETTY.addInitializer(
    initializeAncestryTrees  
)
