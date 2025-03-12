'use strict'

import {initializeMaps} from './maps.js'
import {BETTY} from "@betty.py/betty/main.ts"

await BETTY.addInitializer(
    initializeMaps // eslint-disable-line @typescript-eslint/no-unsafe-argument
)
