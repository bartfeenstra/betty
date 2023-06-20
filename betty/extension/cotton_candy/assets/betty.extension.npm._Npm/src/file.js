'use strict'

const _CLOSE_KEYS = ['Escape']
const _PREVIOUS_FILE_KEYS = ['ArrowLeft']
const _NEXT_FILE_KEYS = ['ArrowRight']

let _positionX = null
let _positionY = null

function _initializeFiles () {
  _initializeFileExtendedOpen()
  _initializeFileExtendedClose()
  _initializeFileExtendedKeyPresses()
}

function _initializeFileExtendedOpen () {
  const links = document.getElementsByClassName('file-extended-open')
  for (let i = 0; i < links.length; i++) {
    const link = links[i]
    link.addEventListener('click', _openExtended)
  }
}

function _openExtended () {
  _positionX = window.scrollX
  _positionY = window.scrollY
}

function _initializeFileExtendedClose () {
  const links = document.getElementsByClassName('file-extended-close')
  for (let i = 0; i < links.length; i++) {
    const link = links[i]
    link.addEventListener('click', _closeExtended)
  }
}

function _closeExtended (e) {
  window.location = '#'
  window.scrollTo({
    left: _positionX,
    top: _positionY
  })
  _positionX = null
  _positionY = null
  e.preventDefault()
}

function _initializeFileExtendedKeyPresses () {
  document.addEventListener('keydown', function (e) {
    if (_CLOSE_KEYS.indexOf(e.key) !== -1) {
      const close = document.querySelector('.file-extended:target .file-extended-close a')
      if (close) {
        close.click()
      }
    } else if (_PREVIOUS_FILE_KEYS.indexOf(e.key) !== -1) {
      const previous = document.querySelector('.file-extended:target .file-extended-previous a')
      if (previous) {
        previous.click()
      }
    } else if (_NEXT_FILE_KEYS.indexOf(e.key) !== -1) {
      const next = document.querySelector('.file-extended:target .file-extended-next a')
      if (next) {
        next.click()
      }
    }
  })
}

document.addEventListener('DOMContentLoaded', _initializeFiles)
