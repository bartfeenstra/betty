"use strict"

import { initializeFullScreenControls } from "@betty.py/betty/full-screen.ts"
import "./main.scss"
import "bootstrap/js/dist/collapse"
import "bootstrap/js/dist/modal"
import { BETTY } from "@betty.py/betty/main.ts"

await BETTY.addInitializer(initializeFullScreenControls)
