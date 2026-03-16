"use strict"

function htmlToElement(html: string): HTMLElement {
    const template = document.createElement("template")
    template.innerHTML = html
    const element = template.content.firstChild
    if (element === null) {
        throw new Error("Template does not contain an HTML element.")
    }
    return element as HTMLElement
}

export {
    htmlToElement,
}
