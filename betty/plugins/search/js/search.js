'use strict'

import searchStyle from './search.css' // eslint-disable-line no-unused-vars

import index from './index.json'
import configuration from './configuration.js'

const enterSearchKeyCodes = [
  // "s".
  83
]

const hideSearchKeyCodes = [
  // Escape.
  27
]

const nextKeyCodes = [
  // Arrow down.
  40
]

const previousKeyCodes = [
  // Arrow up.
  38
]

const searchElement = document.getElementById('search')
const searchQueryElement = document.getElementById('search-query')
const searchResultsInjector = document.createElement('div')

function initializeSearch () {
  // Prevent default form submission behaviors, such as HTTP requests.
  searchElement.addEventListener('submit', () => {
    return false
  })

  searchQueryElement.addEventListener('keyup', search)

  // Allow keyboard navigation through the results.
  searchQueryElement.addEventListener('keydown', (e) => {
    navigateResults(e.which)
  })
  searchResultsInjector.addEventListener('keydown', (e) => {
    navigateResults(e.which)
  })

  // Allow navigation into and out of the search.
  document.addEventListener('keyup', (e) => {
    if (enterSearchKeyCodes.includes(e.which)) {
      searchQueryElement.focus()
    }
  })
  searchQueryElement.addEventListener('focus', showSearchResults)
  document.addEventListener('mousedown', (e) => {
    if (!searchQueryElement.contains(e.target) && !searchResultsInjector.contains(e.target)) {
      hideSearchResults()
      searchQueryElement.blur()
    }
  })
  document.addEventListener('keydown', (e) => {
    if (hideSearchKeyCodes.includes(e.which)) {
      hideSearchResults()
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

    if (document.activeElement.classList.contains('search-result-target')) {
      // If the focus lies on a search result, focus on the previous search result if there is one.
      let previousSearchResultContainer = document.activeElement.closest('.search-result').previousElementSibling
      if (previousSearchResultContainer) {
        previousSearchResultContainer.querySelector('.search-result-target').focus()
        return
      }

      // If no previous search result exists, focus on the query input element.
      searchQueryElement.focus()
    }
  } else if (nextKeyCodes.includes(keyCode)) {
    // If the focus lies on the query input element, focus on the first search result.
    if (document.activeElement === searchQueryElement) {
      searchResultsInjector.getElementsByClassName('search-result-target')[0].focus()
      return
    }
    // If the focus lies on a search result, focus on the next search result if there is one.
    if (document.activeElement.classList.contains('search-result-target')) {
      let nextSearchResultContainer = document.activeElement.closest('.search-result').nextElementSibling
      if (nextSearchResultContainer) {
        nextSearchResultContainer.querySelector('.search-result-target').focus()
      }
    }
  }
}

function setSearchResults (results) {
  searchResultsInjector.innerHTML = renderResults(results)
}

function showSearchResults () {
  document.body.appendChild(searchResultsInjector)
}

function hideSearchResults () {
  if (!searchResultsInjector.parentNode) {
    return
  }
  searchResultsInjector.parentNode.removeChild(searchResultsInjector)
}

function search () {
  const results = index.filter((result) => match(this.value, result.text))
  setSearchResults(results)
  showSearchResults()
}

function match (query, haystack) {
  for (let queryPart of query.toLowerCase().split(/\s/).filter((x) => x)) {
    if (!haystack.includes(queryPart)) {
      return false
    }
  }
  return true
}

function renderResults (results) {
  return configuration.resultsContainerTemplate
    .replace('## results ##', results.map(renderResult).join(''))
}

function renderResult (result) {
  return configuration.resultContainerTemplate
    .replace('## result ##', result.result)
}

export {
  initializeSearch as betty
}
