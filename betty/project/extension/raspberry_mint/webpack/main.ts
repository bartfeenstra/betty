'use strict'

import './css/main.scss'
import "bootstrap/js/dist/collapse"
import "bootstrap/js/dist/modal"
import {Search} from './search.ts'
import {BETTY} from "@betty.py/betty/main.ts";
import {initializeScrollPreventions} from "@betty.py/betty/scroll-prevention.ts"

new Search()
BETTY.addInitializer(initializeScrollPreventions)
