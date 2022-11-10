'use strict'

function initializeToggles () {
  var toggles = document.getElementsByClassName('show-toggle')
  for (var i = 0; i < toggles.length; i++) {
    initializeToggle(toggles[i])
  }
}

function initializeToggle (toggle) {
  toggle.addEventListener('click', function () {
    var container = getContainer(this)
    if (container) {
      container.classList.toggle('show-shown')
    }
  })
}

function getContainer (node) {
  while (node.parentNode) {
    node = node.parentNode
    if (node.classList.contains('show')) {
      return node
    }
  }
}

document.addEventListener('DOMContentLoaded', initializeToggles)
