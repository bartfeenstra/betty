'use strict'

import mapsStyle from './maps.css' // eslint-disable-line no-unused-vars

import * as L from 'leaflet'
import leafletStyle from 'leaflet/dist/leaflet.css' // eslint-disable-line no-unused-vars
import leafletMarkerIconImage from 'leaflet/dist/images/marker-icon.png'
import leafletMarkerIcon2xImage from 'leaflet/dist/images/marker-icon-2x.png'
import leafletMarkerShadowImage from 'leaflet/dist/images/marker-shadow.png'
import { GestureHandling } from 'leaflet-gesture-handling'
import 'leaflet-gesture-handling/dist/leaflet-gesture-handling.css' // eslint-disable-line no-unused-vars
import configuration from './configuration.json'

L.Map.addInitHook('addHandler', 'gestureHandling', GestureHandling)

let mapCount = 0

function initializePlaceLists () {
  const placeLists = document.getElementsByClassName('places')
  for (const placeList of placeLists) {
    initializePlaceList(placeList)
  }
}

function initializePlaceList (placeList) {
  const mapArea = placeList.getElementsByClassName('map')[0]
  mapArea.id = (++mapCount).toString()

  const map = L.map(mapArea.id, {
    gestureHandling: true
  })

  // Build the attribution layer.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  // Build place markers.
  const markerGroup = L.featureGroup()
  Promise.all(Array.from(placeList.querySelectorAll('[data-betty-place]')).map((placeDatum) => {
    return fetch(placeDatum.dataset.bettyPlace)
      .then((response) => response.json())
      .then((place) => {
        if (!place.coordinates) {
          return
        }
        const marker = L.marker([place.coordinates.latitude, place.coordinates.longitude], {
          icon: new BettyIcon()
        }).addTo(map)
        marker.bindPopup(placeDatum.innerHTML)
        markerGroup.addLayer(marker)
      })
  }))
    .then(() => {
      map.fitBounds(markerGroup.getBounds(), {
        maxZoom: 9
      })
    })
}

const BettyIcon = L.Icon.Default.extend({
  options: {
    imagePath: configuration.rootPath,
    iconUrl: leafletMarkerIconImage.replace(/^\/+/, ''),
    iconRetinaUrl: leafletMarkerIcon2xImage.replace(/^\/+/, ''),
    shadowUrl: leafletMarkerShadowImage.replace(/^\/+/, '')
  }
})

document.addEventListener('DOMContentLoaded', initializePlaceLists)
