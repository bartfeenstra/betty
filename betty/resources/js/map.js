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
      attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>'
      // maxZoom: 18,
      // id: 'mapbox.streets',
      // accessToken: 'your.mapbox.access.token'
    }).addTo(map)
  }
}

export { initializeMaps }
