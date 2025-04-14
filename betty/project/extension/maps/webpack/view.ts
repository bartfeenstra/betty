"use strict"

import Map from "ol/Map"
import { AnimationOptions } from "ol/View"

function zoomByDelta(map: Map, delta: number, options: AnimationOptions): void {
    const view = map.getView()
    const currentZoom = view.getZoom()
    if (currentZoom !== undefined) {
        const newZoom = view.getConstrainedZoom(currentZoom + delta)
        if (view.getAnimating()) {
            view.cancelAnimations()
        }
        view.animate({
            ...options,
            zoom: newZoom,
        })
    }
}

export {
    zoomByDelta,
}
