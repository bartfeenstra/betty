"use strict"

const _CLOSE_KEYS = ["Escape"]
const _PREVIOUS_FILE_KEYS = ["ArrowLeft"]
const _NEXT_FILE_KEYS = ["ArrowRight"]

let _positionX: number | undefined
let _positionY: number | undefined

async function initializeFiles(): Promise<void> { // eslint-disable-line @typescript-eslint/require-await
    _initializeFileExtendedOpen()
    _initializeFileExtendedClose()
    _initializeFileExtendedKeyPresses()
}

function _initializeFileExtendedOpen(): void {
    const links = document.getElementsByClassName("file-extended-open")
    for (const link of links) {
        link.addEventListener("click", _openExtended)
    }
}

function _openExtended(): void {
    _positionX = window.scrollX
    _positionY = window.scrollY
}

function _initializeFileExtendedClose(): void {
    const links = document.getElementsByClassName("file-extended-close")
    for (const link of links) {
        link.addEventListener("click", _closeExtended)
    }
}

function _closeExtended(e: Event): void {
    window.location.href = "#"
    window.scrollTo({
        left: _positionX,
        top: _positionY,
    })
    _positionX = undefined
    _positionY = undefined
    e.preventDefault()
}

function _initializeFileExtendedKeyPresses(): void {
    document.addEventListener("keydown", function (e) {
        if (_CLOSE_KEYS.includes(e.key)) {
            const close = document.querySelector<HTMLElement>(".file-extended:target .file-extended-close a")
            if (close) {
                close.click()
            }
        }
        else if (_PREVIOUS_FILE_KEYS.includes(e.key)) {
            const previous = document.querySelector<HTMLElement>(".file-extended:target .file-extended-previous a")
            if (previous) {
                previous.click()
            }
        }
        else if (_NEXT_FILE_KEYS.includes(e.key)) {
            const next = document.querySelector<HTMLElement>(".file-extended:target .file-extended-next a")
            if (next) {
                next.click()
            }
        }
    })
}

export {
    initializeFiles,
}
