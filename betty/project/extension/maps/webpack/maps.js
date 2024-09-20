'use strict'

import './main.css'

import * as L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import leafletMarkerIconImage from 'leaflet/dist/images/marker-icon.png'
import leafletMarkerIcon2xImage from 'leaflet/dist/images/marker-icon-2x.png'
import leafletMarkerShadowImage from 'leaflet/dist/images/marker-shadow.png'
import { GestureHandling } from 'leaflet-gesture-handling'
import 'leaflet.markercluster/dist/leaflet.markercluster.js'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.fullscreen/Control.FullScreen.js'
import 'leaflet.fullscreen/Control.FullScreen.css'
import 'leaflet-gesture-handling/dist/leaflet-gesture-handling.css'

L.Map.addInitHook('addHandler', 'gestureHandling', GestureHandling)

let mapCount = 0

async function initializePlaceLists () {
  const placeLists = document.getElementsByClassName('places')
  await Promise.allSettled(Array.from(placeLists).map(placeList => initializePlaceList(placeList)))
}

async function initializePlaceList (placeList) {
  const mapArea = placeList.getElementsByClassName('map')[0]
  mapArea.id = (++mapCount).toString()

  const map = L.map(mapArea.id, {
    gestureHandling: true,
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: 'topleft'
    }
  })

  // Build the attribution layer.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  // Build place markers.
  const markerGroup = L.markerClusterGroup({
    showCoverageOnHover: false
  })
  map.addLayer(markerGroup)
  await Promise.all(Array.from(placeList.querySelectorAll('[data-betty-place]')).map(async (placeDatum) => {
    const response = await fetch(placeDatum.dataset.bettyPlace)
    const place = await response.json()
    if (!place.coordinates) {
      return
    }
    const marker = L.marker([place.coordinates.latitude, place.coordinates.longitude], {
      icon: new BettyIcon()
    })
    marker.bindPopup(placeDatum.innerHTML)
    markerGroup.addLayer(marker)
  }))
  map.fitBounds(markerGroup.getBounds(), {
    maxZoom: 9
  })
}

const BettyIcon = L.Icon.Default.extend({
  options: {
    iconUrl: leafletMarkerIconImage,
    iconRetinaUrl: leafletMarkerIcon2xImage,
    shadowUrl: leafletMarkerShadowImage
  }
})

export {
  initializePlaceLists,
}
