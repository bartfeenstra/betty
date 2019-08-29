'use strict'

import searchStyle from './search.css' // eslint-disable-line no-unused-vars

import ancestry from './ancestry.json'
import configuration from './configuration.js'

const nextKeyCodes = [
    // Arrow right.
    39,
    // Arrow down.
    40,
]

const previousKeyCodes = [
    // Arrow left.
    37,
    // Arrow up.
    38,
]


const searchElement = document.getElementById('search')

const searchQueryElement = document.getElementById('search-query')

let container

function initializeSearch () {
  // Prevent default form submission behaviors, such as HTTP requests.
  searchElement.addEventListener('submit', () => {
    return false
  })

  searchQueryElement.addEventListener('keypress', search)

  // Allow keyboard navigation through the results.
  searchQueryElement.addEventListener('keydown', (e) => {
    navigateResults(e.which)
  })

  document.addEventListener('keydown', (e) => {
    // Allow the results to be hidden using the escape key.
    if (27 === e.which) {
      hideContainer()
    }
  })
  // @todo When the query input OR a search result has the focus, allow arrow keys (previous, next) and the tab (next) button to
  // @todo change the focus to specific search results.
  // @todo
  // @todo
  // @todo
  // @todo
}

// @todo Create the container separately, because a new search may be started while the container from a previous search is still active
// @todo Close the container under certain conditions, such as when an element outside the container or query input is focused.
// @todo
// @todo
// @todo

function navigateResults(keyCode) {
  // @todo This breaks if there are no results.
  if (previousKeyCodes.includes(keyCode)) {
    console.log('PREVIOUS')
    if (document.activeElement === searchQueryElement) {
      return
    }
    if (document.activeElement.classList.contains('search-result')) {
      if (!document.activeElement.previousElementSibling) {
        console.log(searchQueryElement)
        searchQueryElement.focus()
      }
      console.log(document.activeElement.previousElementSibling)
      document.activeElement.previousElementSibling.focus()
    }
  }
  else if (nextKeyCodes.includes(keyCode)) {
    console.log('NEXT')
    if (document.activeElement === searchQueryElement) {
      console.log(container.getElementsByClassName('search-result')[0])
      container.getElementsByClassName('search-result')[0].focus()
    }
    else if (document.activeElement.classList.contains('search-result')) {
      if (!document.activeElement.nextElementSibling) {
        return
      }
      console.log(document.activeElement.nextElementSibling)
      document.activeElement.nextElementSibling.focus()
    }
  }
}

function getContainer() {
  if (container != null) {
    return container
  }
  container = document.createElement('div')
  container.id = 'search-results-container'
  return container
}

function configureContainer(content) {
  getContainer().innerHTML = content
}

function showContainer() {
  document.body.appendChild(getContainer())
}

function hideContainer() {
  const container = getContainer()
  if (!container.parentNode) {
    return
  }
  container.parentNode.removeChild(container)
}

function search() {
  const results = searchPeople(this.value)
  configureContainer(renderResults(results))
  showContainer()
}

function match(query, haystack) {
  haystack = haystack.toLowerCase()
  for (let query_part of query.split(/\s/)) {
    if (haystack.includes(query)) {
      return true
    }
  }
  return false
}

function searchPeople(query) {
  return Object.values(ancestry.people)
      .filter((person) => person.family_name && match(query, person.family_name) || person.individual_name && match(query, person.individual_name))
      // @todo Use generic labels and get URLs from Python.
      .map((person) => new Result(person.individual_name + ' ' + person.family_name, 'person/' + person.id))
}

function renderResults(results) {
  return configuration.resultsTemplate
      .replace('## results ##', results.map(renderResult).join(''))
}

function renderResult(result) {
  return configuration.resultTemplate
      .replace('## result_label ##', result.label)
      .replace('## result_url ##', result.url)
}

class Result {
  constructor(label, url) {
    this.label = label
    this.url = url
  }
}

export {
  initializeSearch as betty
}
