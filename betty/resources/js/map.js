'use strict'

import * as L from 'leaflet'
import { style } from '../../node_modules/leaflet/dist/leaflet.css' // eslint-disable-line no-unused-vars
import { leafletLayerImage } from '../../node_modules/leaflet/dist/images/layers.png' // eslint-disable-line no-unused-vars
import { leafletLayer2xImage } from '../../node_modules/leaflet/dist/images/layers-2x.png' // eslint-disable-line no-unused-vars
import { leaflerMarkerIconImage } from '../../node_modules/leaflet/dist/images/marker-icon.png' // eslint-disable-line no-unused-vars
import { leafletMarkerIcon2xImage } from '../../node_modules/leaflet/dist/images/marker-icon-2x.png' // eslint-disable-line no-unused-vars
import { leafletMarkerShadowImage } from '../../node_modules/leaflet/dist/images/marker-shadow.png' // eslint-disable-line no-unused-vars
import ancestry from './ancestry.json'

let mapCount = 0

function initializePlaceLists () {
  const placeLists = document.getElementsByClassName('places')
  for (let placeList of placeLists) {
    initializePlaceList(placeList)
  }
}

function initializePlaceList (placeList) {
  const placeData = placeList.querySelectorAll('[data-betty-place-id]')

  const mapArea = placeList.getElementsByClassName('map')[0]
  mapArea.id = (++mapCount).toString()

  let map = L.map(mapArea.id)

  // Build the attribution layer.
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  // Build the icons. We need this, because Leaflet references its image files from CSS, and from JS, but without using
  // imports. This is also why we explicitly import all image files individually in this file.
  L.Icon.Default.prototype.options.imagePath = '/images/leaflet/'

  // Build place markers.
  const markers = []
  for (let placeDatum of placeData) {
    let place = ancestry.places[placeDatum.dataset.bettyPlaceId]
    if (place.coordinates) {
      let marker = L.marker([place.coordinates.latitude, place.coordinates.longitude]).addTo(map)
      marker.bindPopup(placeDatum.innerHTML)
      markers.push(marker)
    }
  }

  // Set the map's position and zoom level.
  const markerGroup = L.featureGroup(markers)
  map.fitBounds(markerGroup.getBounds(), {
    maxZoom: 9
  })
}

export { initializePlaceLists }
