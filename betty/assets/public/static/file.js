'use strict'

var _positionX = null
var _positionY = null

function _initializeFiles () {
  _initializeFileExtendedOpen()
  _initializeFileExtendedClose()
}

function _initializeFileExtendedOpen () {
  var links = document.getElementsByClassName('file-extended-open')
  for (var i = 0; i < links.length; i++) {
    var link = links[i]
    link.addEventListener('click', _openExtended)
  }
}

function _openExtended () {
  _positionX = window.scrollX
  _positionY = window.scrollY
}

function _initializeFileExtendedClose () {
  var links = document.getElementsByClassName('file-extended-close')
  for (var i = 0; i < links.length; i++) {
    var link = links[i]
    link.addEventListener('click', _closeExtended)
  }
}

function _closeExtended (e) {
  window.location = '#'
  window.scrollTo({
    left: _positionX,
    top: _positionY
  })
  e.preventDefault()
}

document.addEventListener('DOMContentLoaded', _initializeFiles)
