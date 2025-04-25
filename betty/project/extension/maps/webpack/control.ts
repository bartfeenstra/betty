"use strict"

import OpenLayersControl from "ol/control/Control"
import OpenLayersMap from "ol/Map"
import { htmlToElement } from "./html.ts"
import { zoomByDelta } from "./view.ts"
import { Map } from "./map.ts"
import Point from "ol/geom/Point"
import VectorSource from "ol/source/Vector"
import Feature from "ol/Feature"
import { AnimationOptions } from "ol/View"
import { getTranslationFromShorthandStatic } from "@betty.py/betty/locale/localizable.ts"

/**
 * @internal
 */
class Control extends OpenLayersControl {
    public constructor(element: HTMLElement, classSuffix: string) {
        element.classList.add("map-control")
        element.classList.add(`map-control-${classSuffix}`)
        super({ element })
    }
}

/**
 * @internal
 */
class FullScreen extends Control {
    public constructor(buttonHtml: string, map: OpenLayersMap) {
        super(document.createElement("div"), "full-screen")

        const button = htmlToElement(buttonHtml.replace("{{{ betty-maps-control-full-screen-target }}}", map.getTargetElement().id))
        this.element.appendChild(button)
    }
}

class _Zoom extends Control {
    public constructor(buttonHtml: string, animationOptions: AnimationOptions, delta: number, classSuffix: string) {
        super(document.createElement("div"), classSuffix)

        const button = htmlToElement(buttonHtml)
        button.addEventListener(
            "click",
            (event) => {
                const map = this.getMap()
                if (map === null) {
                    return
                }
                event.preventDefault()
                zoomByDelta(map, delta, animationOptions)
            },
            false,
        )
        this.element.appendChild(button)
    }
}

/**
 * @internal
 */
class ZoomIn extends _Zoom {
    public constructor(buttonHtml: string, animationOptions: AnimationOptions) {
        super(buttonHtml, animationOptions, 1, "zoom-in")
    }
}

/**
 * @internal
 */
class ZoomOut extends _Zoom {
    public constructor(buttonHtml: string, animationOptions: AnimationOptions) {
        super(buttonHtml, animationOptions, -1, "zoom-out")
    }
}

const selectedPlaceAnchorNameToIndex: Record<string, number> = {
    left: 0,
    top: 1,
    right: 2,
    bottom: 3,
}

const selectedPlaceAnchorCssVariableName = "--betty-map-selected-place-anchor"

/**
 * @internal
 */
class SelectedPlace extends OpenLayersControl {
    private readonly map: Map
    private readonly inner: HTMLElement
    private readonly selectedPlaceSource: VectorSource

    public constructor(map: Map, selectedPlaceSource: VectorSource) {
        super({
            element: htmlToElement(getTranslationFromShorthandStatic(map.options.selectedPlaceHtml, map.locale)),
        })
        this.element.classList.add("map-selected-place")
        this.inner = this.element.getElementsByClassName("map-selected-place-content")[0] as HTMLElement
        for (const closeButton of this.element.getElementsByClassName("map-selected-place-close")) {
            (closeButton as HTMLElement).addEventListener("click", () => {
                this.unselect()
            })
        }
        this.map = map
        this.selectedPlaceSource = selectedPlaceSource
    }

    public async select(placeId: string): Promise<void> {
        this.unselect()
        this.selectedPlaceSource.addFeature(new Feature({
            placeId: placeId,
            geometry: this.map.placeFeatures[placeId].getGeometry(),
        }))
        const response = await fetch(this.map.placeDatas[placeId].previewUrlPath)
        this.inner.innerHTML = await response.text()
        this.element.classList.add("map-selected-place-visible")
        const geometry = this.map.placeFeatures[placeId].getGeometry()
        if (geometry instanceof Point) {
            const anchorName = getComputedStyle(this.inner).getPropertyValue(selectedPlaceAnchorCssVariableName)
            const anchorIndex = selectedPlaceAnchorNameToIndex[anchorName.substring(1, anchorName.length - 1)]
            if (anchorIndex === undefined) { // eslint-disable-line @typescript-eslint/no-unnecessary-condition
                throw new Error(`Invalid value "${anchorName}" for selected place element's ${selectedPlaceAnchorCssVariableName} CSS variable. The value must be one of ${Object.keys(selectedPlaceAnchorNameToIndex).map(name => `"${name}"`).join(", ")}.`)
            }
            const mapSize = this.map.map.getSize()
            if (mapSize === undefined) {
                throw new Error("Map has no size.")
            }
            const selectedPlaceRectangle = this.element.getBoundingClientRect()
            const selectedPlaceSize = [selectedPlaceRectangle.width, selectedPlaceRectangle.height]
            const center = [mapSize[0] / 2, mapSize[1] / 2]
            const direction = Math.abs(anchorIndex % 2)
            const selectedPlacePixel = this.map.map.getPixelFromCoordinate(geometry.getCoordinates())
            const anchorOffset = selectedPlaceSize[direction] + this.map.options.viewPadding[anchorIndex]
            let centerOffset: number
            if (anchorIndex < 2) {
                centerOffset = Math.min(0, selectedPlacePixel[direction] - anchorOffset)
            }
            else {
                centerOffset = Math.max(0, Math.abs(mapSize[direction] - selectedPlacePixel[direction] - anchorOffset))
            }
            if (centerOffset !== 0) {
                center[direction] += centerOffset
                this.map.view.animate({
                    ...this.map.viewAnimationOptions,
                    center: this.map.map.getCoordinateFromPixel(center),
                })
            }
        }
    }

    public unselect(): void {
        this.selectedPlaceSource.clear()
        this.element.classList.remove("map-selected-place-visible")
        this.inner.innerHTML = ""
    }
}

export {
    FullScreen,
    SelectedPlace,
    ZoomIn,
    ZoomOut,
}
