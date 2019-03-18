'use strict'

import * as L from 'leaflet'
import { style } from '../../node_modules/leaflet/dist/leaflet.css' // eslint-disable-line no-unused-vars
import ancestry from './ancestry.json'

function initializeMaps () {
  const mapContainers = document.getElementsByClassName('map')
  for (let mapContainer of mapContainers) {
    initializeMap(mapContainer)
  }
}

function initializeMap (mapContainer) {
  let map = L.map(mapContainer.id)

  // Build the attribution layer.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  // Build place markers.
  const markers = []
  const placeIds = mapContainer.dataset.placeIds.split(',')
  for (let placeId of placeIds) {
    let place = ancestry.places[placeId]
    if (place.coordinates) {
      let marker = L.marker([place.coordinates.latitude, place.coordinates.longitude]).addTo(map)
      marker.bindPopup(`<a href="/place/${place.id}">${place.label}</a>`)
      markers.push(marker)
    }
  }

  // Set the map's position and zoom level.
  const markerGroup = L.featureGroup(markers)
  map.fitBounds(markerGroup.getBounds(), {
    maxZoom: 9
  })
}

export { initializeMaps }
