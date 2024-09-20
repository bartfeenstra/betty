'use strict'

async function initializeToggles () :Promise<void> { // eslint-disable-line @typescript-eslint/require-await
  const toggles = document.getElementsByClassName('show-toggle')
  for (const toggle of toggles) {
    initializeToggle(toggle as Element)
  }
}

function initializeToggle (toggle: Element) :void {
  toggle.addEventListener('click', (event: PointerEvent) => {
    const container: Element | null = getContainer(event.target as Element) // eslint-disable-line @typescript-eslint/no-unsafe-assignment
    if (container) {
      container.classList.toggle('show-shown')
    }
  })
}

function getContainer (node: Element): Element | null {
  const parentNode = node.parentNode as Element | null
  if (!parentNode) {
    return
  }
  if (parentNode.classList.contains('show')) {
    return parentNode
  }
  return getContainer(parentNode)
}

export {
  initializeToggles,
}
