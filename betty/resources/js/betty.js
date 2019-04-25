'use strict'

import { style } from '../css/betty.css' // eslint-disable-line no-unused-vars
import { initializePlaceLists } from './map'
import { initializeAncestryTrees } from './tree'

document.addEventListener('DOMContentLoaded', () => {
  initializePlaceLists()
  initializeAncestryTrees()
})
