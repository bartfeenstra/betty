'use strict'

const attributeName = 'data-betty-scroll-prevention-target'

function initializeScrollPrevention(scrollable: HTMLElement): void {
    const targetId = scrollable.dataset.bettyScrollPreventionTarget
    if (targetId === undefined) {
        throw new Error(`Element does not have the expected "${attributeName}" attribute.`)
    }
    const target = document.getElementById(targetId)
    scrollable.addEventListener('wheel', event => {
        console.log('WHEEL')
        console.log(target)
        // @todo Do not prevent scrolling if the scrollable is fullscreen!!!
        // @todo Also do not prevent scrolling if CTRL+mouse is used, or two fingers
        event.stopPropagation()
        event.preventDefault()
        target.classList.add('betty-scroll-prevention-visible')
        // @todo Ensure no race conditions!
        window.setTimeout(() => {
            target.classList.remove('betty-scroll-prevention-visible')
        }, 500)
    }, {
        capture: true,
    })
}

async function initializeScrollPreventions(element: HTMLElement): Promise<void> { // eslint-disable-line @typescript-eslint/require-await
    for (const scrollable of element.querySelectorAll(`[${attributeName}]`) as HTMLElement[]) {
        console.log('INIT SCROLL PREVENTION')
        console.log(scrollable)
        initializeScrollPrevention(scrollable)
    }
}

export {
    initializeScrollPrevention,
    initializeScrollPreventions,
}
