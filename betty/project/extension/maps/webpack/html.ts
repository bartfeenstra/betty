'use strict'

function htmlToElement(html: string): HTMLElement {
    const template = document.createElement('template')
    template.innerHTML = html
    return template.content.firstChild
}

export {
    htmlToElement,
}