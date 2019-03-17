'use strict'

import * as L from 'leaflet'
import { style } from '../../node_modules/leaflet/dist/leaflet.css' // eslint-disable-line no-unused-vars

function initializeMaps () {
  const mapContainers = document.getElementsByClassName('map')
  for (let mapContainer of mapContainers) {
    console.log(mapContainer)
    console.log(mapContainer.dataset)
    let map = L.map(mapContainer.id).setView([mapContainer.dataset.latitude, mapContainer.dataset.longitude], 13)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map)
  }
}

export { initializeMaps }
