'use strict';

import {map as LMap} from 'leaflet'

import style from '../node_modules/leaflet/dist/leaflet.css'

const mapContainers = document.getElementsByClassName('map');
for (let mapContainer of mapContainers) {
    let map = LMap(mapContainer.id).setView(mapContainer.dataset.latitude, mapContainer.dataset.longitude);
    console.log(mapContainer);
}
