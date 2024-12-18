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

async function initializeMaps () {
  const maps = document.getElementsByClassName('map')
  await Promise.allSettled(Array.from(maps).map(map => initializeMap(map)))
}

async function initializeMap (map) {
  map.id = (++mapCount).toString()

  const leafletMap = L.map(map.id, {
    gestureHandling: true,
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: 'topleft'
    }
  })

  // Build the attribution layer.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(leafletMap)

  // Build place markers.
  const markerGroup = L.markerClusterGroup({
    showCoverageOnHover: false
  })
  leafletMap.addLayer(markerGroup)
  const placesData = JSON.parse(map.dataset.bettyPlaces)
  await Promise.all(placesData.map(async (placeData) => {
    const [placeUrl, placeLatitude, placeLongitude, placeLabel] = placeData
    const marker = L.marker([placeLatitude, placeLongitude], {
      icon: new BettyIcon()
    })
    marker.bindPopup(`<p><a href="${placeUrl}">${placeLabel}</a></p>`)
    markerGroup.addLayer(marker)
  }))
  leafletMap.fitBounds(markerGroup.getBounds(), {
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
  initializeMaps,
}
