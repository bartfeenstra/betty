'use strict'

import searchStyle from './search.css' // eslint-disable-line no-unused-vars

import index from './index.json'
import configuration from './configuration.js'

const hideSearchKeyCodes = [
  // Escape.
  27
]

const nextKeyCodes = [
  // Arrow right.
  39,
  // Arrow down.
  40
]

const previousKeyCodes = [
  // Arrow left.
  37,
  // Arrow up.
  38
]

const searchElement = document.getElementById('search')
const searchQueryElement = document.getElementById('search-query')
const container = document.createElement('div')

function initializeSearch () {
  // Initialize the container.
  container.id = 'search-results-container'

  // Prevent default form submission behaviors, such as HTTP requests.
  searchElement.addEventListener('submit', () => {
    return false
  })

  searchQueryElement.addEventListener('keyup', search)

  // Allow keyboard navigation through the results.
  searchQueryElement.addEventListener('keydown', (e) => {
    navigateResults(e.which)
  })
  container.addEventListener('keydown', (e) => {
    navigateResults(e.which)
  })

  document.addEventListener('keydown', (e) => {
    if (hideSearchKeyCodes.includes(e.which)) {
      hideContainer()
      searchQueryElement.blur()
    }
  })
}

function navigateResults (keyCode) {
  if (previousKeyCodes.includes(keyCode)) {
    // If the focus lies on the query input element, do nothing, because there are no previous search results.
    if (document.activeElement === searchQueryElement) {
      return
    }

    if (document.activeElement.classList.contains('search-result')) {
      // If the focus lies on a search result, focus on the previous search result if there is one.
      let previousSearchResultContainer = document.activeElement.closest('.search-result-container').previousElementSibling
      if (previousSearchResultContainer) {
        previousSearchResultContainer.querySelector('.search-result').focus()
        return
      }

      // If no previous search result exists, focus on the query input element.
      searchQueryElement.focus()
    }
  } else if (nextKeyCodes.includes(keyCode)) {
    // If the focus lies on the query input element, focus on the first search result.
    if (document.activeElement === searchQueryElement) {
      container.getElementsByClassName('search-result')[0].focus()
      return
    }
    // If the focus lies on a search result, focus on the next search result if there is one.
    if (document.activeElement.classList.contains('search-result')) {
      let nextSearchResultContainer = document.activeElement.closest('.search-result-container').nextElementSibling
      if (nextSearchResultContainer) {
        nextSearchResultContainer.querySelector('.search-result').focus()
      }
    }
  }
}

function configureContainer (content) {
  container.innerHTML = content
}

function showContainer () {
  document.body.appendChild(container)
}

function hideContainer () {
  if (!container.parentNode) {
    return
  }
  container.parentNode.removeChild(container)
}

function search () {
  const results = index.filter((result) => match(this.value, result.text))
  configureContainer(renderResults(results))
  showContainer()
}

function match (query, haystack) {
  haystack = haystack.toLowerCase()
  for (let queryPart of query.split(/\s/).filter((x) => x)) {
    if (!haystack.includes(queryPart)) {
      return false
    }
  }
  return true
}

function renderResults (results) {
  return configuration.resultsTemplate
    .replace('## results ##', results.map(renderResult).join(''))
}

function renderResult (result) {
  return configuration.resultTemplate
    .replace('## result_label ##', result.label)
    .replace('## result_url ##', result.url)
}

export {
  initializeSearch as betty
}
