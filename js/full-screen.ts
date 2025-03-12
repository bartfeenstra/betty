'use strict'

const attributeName = 'data-betty-full-screen-target'

async function toggleFullScreen(element: Element): Promise<void> {
    const document = element.ownerDocument
    const currentFullScreenElement = document.fullscreenElement
    if (currentFullScreenElement) {
        await document.exitFullscreen()
    }
    if (currentFullScreenElement != element) {
        await element.requestFullscreen()
    }
}

function initializeFullScreenControl(control: HTMLElement): void {
    const target = control.dataset.bettyFullScreenTarget
    if (target === undefined) {
        throw new Error(`Element does not have the expected "${attributeName}" attribute.`)
    }
    control.addEventListener('click', () => {
        void (async (): Promise<void> => {
            await toggleFullScreen(document.getElementById(target))
        })()
    })
}

async function initializeFullScreenControls(element: HTMLElement): Promise<void> { // eslint-disable-line @typescript-eslint/require-await
    for (const control of element.querySelectorAll(`[${attributeName}]`) as HTMLElement[]) {
        initializeFullScreenControl(control)
    }
}

export {
    toggleFullScreen,
    initializeFullScreenControl,
    initializeFullScreenControls,
}
