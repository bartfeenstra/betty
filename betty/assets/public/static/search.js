'use strict'

var enterSearchKeyCodes = [
  // "s".
  83
]

var hideSearchKeyCodes = [
  // Escape.
  27
]

var nextKeyCodes = [
  // Arrow down.
  40
]

var previousKeyCodes = [
  // Arrow up.
  38
]

function Search() {
  this._query = null
  this._search = document.getElementById('search')
  this._indexUrl = this._search.dataset.bettySearchIndex
  this._form = this._search.getElementsByTagName('form').item(0)
  this._queryElement = document.getElementById('search-query')
  this._resultsContainer = document.getElementById('search-results-container')
  var _this = this

  // Prevent default form submission behaviors, such as HTTP requests.
  this._form.addEventListener('submit', function () {
    return false
  })

  this._queryElement.addEventListener('keyup', function () {
    _this.perform(this.value)
  })

  // Allow keyboard navigation through the results.
  this._queryElement.addEventListener('keydown', function (e) {
    _this._navigateResults(e.which)
  })
  this._resultsContainer.addEventListener('keydown', function (e) {
    _this._navigateResults(e.which)
  })

  // Allow navigation into and out of the search.
  document.addEventListener('keyup', function (e) {
    if (enterSearchKeyCodes.includes(e.which)) {
      _this._queryElement.focus()
    }
  })
  this._queryElement.addEventListener('focus', function() {
    _this.showSearchResults()
  })
  document.addEventListener('mousedown', function (e) {
    if (!_this._queryElement.contains(e.target) && !_this._resultsContainer.contains(e.target)) {
      _this.hideSearchResults()
      _this._queryElement.blur()
    }
  })
  document.addEventListener('keydown', function (e) {
    if (hideSearchKeyCodes.includes(e.which)) {
      _this.hideSearchResults()
      _this._queryElement.blur()
    }
  })
}

Search.prototype._navigateResults = function(keyCode) {
  if (previousKeyCodes.includes(keyCode)) {
    // If the focus lies on the query input element, do nothing, because there are no previous search results.
    if (document.activeElement === this._queryElement) {
      return
    }

    if (document.activeElement.classList.contains('search-result-target')) {
      // If the focus lies on a search result, focus on the previous search result if there is one.
      var previousSearchResultContainer = document.activeElement.closest('.search-result').previousElementSibling
      if (previousSearchResultContainer) {
        previousSearchResultContainer.querySelector('.search-result-target').focus()
        return
      }

      // If no previous search result exists, focus on the query input element.
      this._queryElement.focus()
    }
  } else if (nextKeyCodes.includes(keyCode)) {
    // If the focus lies on the query input element, focus on the first search result.
    if (document.activeElement === this._queryElement) {
      this._resultsContainer.getElementsByClassName('search-result-target')[0].focus()
      return
    }
    // If the focus lies on a search result, focus on the next search result if there is one.
    if (document.activeElement.classList.contains('search-result-target')) {
      var nextSearchResultContainer = document.activeElement.closest('.search-result').nextElementSibling
      if (nextSearchResultContainer) {
        nextSearchResultContainer.querySelector('.search-result-target').focus()
      }
    }
  }
}

Search.prototype._setSearchResults = function(results) {
  this._resultsContainer.innerHTML = this._renderResults(results)
}

Search.prototype.showSearchResults = function() {
  this._search.classList.add('focus')
}

Search.prototype.hideSearchResults = function() {
  this._search.classList.remove('focus')
}

Search.prototype._performCacheQuery = function (query) {
  this._query = query
}

Search.prototype._performFromCachedQuery = function () {
  var query = this._query
  this._query = null
  var _this = this
  this._setSearchResults(this._index.filter(function (result) {
    return _this._match(query, result.text)
  }))
}

Search.prototype._performCached = function (query) {
  this._performCacheQuery(query)
  this._performFromCachedQuery()
}

Search.prototype._performUncached = function(query) {
  this._query = query
  this.perform = this._performCacheQuery
  var _this = this
  var indexRequest = new XMLHttpRequest()
  indexRequest.open('GET', this._indexUrl)
  indexRequest.addEventListener('load', function (e) {
    var index = JSON.parse(indexRequest.response)
    _this._index = index.index
    _this._resultContainerTemplate = index.resultContainerTemplate
    _this._resultsContainerTemplate = index.resultsContainerTemplate
    _this.perform = _this._performCached
    _this._performFromCachedQuery()
  })
  indexRequest.send()
}

Search.prototype.perform = Search.prototype._performUncached

Search.prototype._match = function(query, haystack) {
  var queryParts = query.toLowerCase().split(/\s/)
  for (var i in queryParts) {
    if (!haystack.includes(queryParts[i])) {
      return false
    }
  }
  return true
}

Search.prototype._renderResults = function(results) {
  var _this = this
  return this._resultsContainerTemplate
      .replace('<!-- betty-search-results -->', results.map(function(result) {
        return _this._renderResult(result)
      }).join(''))
}

Search.prototype._renderResult = function(result) {
  return this._resultContainerTemplate
      .replace('<!-- betty-search-result -->', result.result)
}

document.addEventListener('DOMContentLoaded', function() {
  new Search('search')
})
