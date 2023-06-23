'use strict'

function initializeToggles () {
  const toggles = document.getElementsByClassName('show-toggle')
  for (let i = 0; i < toggles.length; i++) {
    initializeToggle(toggles[i])
  }
}

function initializeToggle (toggle) {
  toggle.addEventListener('click', function () {
    const container = getContainer(this)
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
