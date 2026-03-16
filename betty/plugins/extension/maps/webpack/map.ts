"use strict"

import Point from "ol/geom/Point"
import Feature from "ol/Feature"
import { FeatureLike } from "ol/Feature"
import OpenLayersMap from "ol/Map"
import OSM from "ol/source/OSM"
import TileLayer from "ol/layer/Tile"
import View, { AnimationOptions } from "ol/View"
import VectorSource from "ol/source/Vector"
import VectorLayer from "ol/layer/Vector"
import Style from "ol/style/Style"
import { boundingExtent, getCenter } from "ol/extent"
import { mouseOnly, platformModifierKeyOnly } from "ol/events/condition"
import Kinetic from "ol/Kinetic"
import DoubleClickZoom from "ol/interaction/DoubleClickZoom"
import DragPan from "ol/interaction/DragPan"
import DragZoom from "ol/interaction/DragZoom"
import KeyboardPan from "ol/interaction/KeyboardPan"
import KeyboardZoom from "ol/interaction/KeyboardZoom"
import MouseWheelZoom from "ol/interaction/MouseWheelZoom"
import PinchZoom from "ol/interaction/PinchZoom"
import { FullScreen, SelectedPlace, ZoomIn, ZoomOut } from "./control.ts"
import { useGeographic } from "ol/proj"
import Icon from "ol/style/Icon.js"
import Cluster from "ol/source/Cluster"
import { BETTY } from "@betty.py/betty/main.ts"
import { easeOut } from "ol/easing"
import { IconAnchorUnits } from "ol/style/Icon"
import { getTranslationFromShorthandStatic, ShorthandStaticTranslations } from "@betty.py/betty/locale/localizable.ts"

const kinetic = new Kinetic(-0.005, 0.05, 100)

async function initializeMap(element: HTMLElement, options: MapOptions, locale: string): Promise<void> {
    const map = new Map(element, options, locale)
    await map.initialize()
}

async function initializeMaps(element: HTMLElement, options: MapOptions, locale: string): Promise<void> {
    for (const mapElement of element.getElementsByClassName("map")) {
        await initializeMap(mapElement as HTMLElement, options, locale)
    }
}

interface PlaceData {
    id: string
    latitude: number
    longitude: number
    previewUrlPath: string
}

interface MapOptions {
    viewPadding: [number, number, number, number]
    clusterMaximumFeatureDistance: number
    clusterMinimumClusterDistance: number
    fullScreenControlButtonHtml: ShorthandStaticTranslations
    zoomInControlButtonHtml: ShorthandStaticTranslations
    zoomOutControlButtonHtml: ShorthandStaticTranslations
    selectedPlaceHtml: ShorthandStaticTranslations
    markerPlaceSvg: string
    markerPlaceAnchor: [number, number]
    markerPlaceSelectedSvg: string
    markerPlaceCluster1Svg: string
    markerPlaceCluster10Svg: string
    markerPlaceCluster100Svg: string
    markerPlaceCluster1000Svg: string
}

function newIconStyle(svg: string, anchor: [number, number], anchorUnits: IconAnchorUnits): Style {
    return new Style({
        image: new Icon({
            src: `data:image/svg+xml;base64,${btoa(svg)}`,
            anchorXUnits: anchorUnits,
            anchorYUnits: anchorUnits,
            anchor,
        }),
    })
}

class Map {
    public readonly placeDatas: Record<string, PlaceData>
    public readonly map: OpenLayersMap
    public readonly placeFeatures: Record<string, Feature>
    public readonly options: MapOptions
    private readonly placeCluster: Cluster
    public readonly view: View
    public readonly selectedPlace: SelectedPlace
    public readonly viewAnimationOptions: AnimationOptions
    private readonly placeStyle: Style
    private readonly placeSelectedStyle: Style
    private readonly placeClusterStyles: Record<number, Style>
    private readonly embedded: boolean
    public readonly locale: string

    public constructor(mapElement: HTMLElement, options: MapOptions, locale: string) {
        useGeographic()

        this.embedded = mapElement.classList.contains("map-embedded")

        this.options = options
        this.locale = locale
        this.viewAnimationOptions = {
            easing: easeOut,
            duration: 500,
        }

        this.placeStyle = newIconStyle(this.options.markerPlaceSvg, this.options.markerPlaceAnchor, "pixels")
        this.placeSelectedStyle = newIconStyle(this.options.markerPlaceSelectedSvg, this.options.markerPlaceAnchor, "pixels")
        this.placeClusterStyles = {
            1: newIconStyle(this.options.markerPlaceCluster1Svg, [0.5, 0.5], "fraction"),
            10: newIconStyle(this.options.markerPlaceCluster10Svg, [0.5, 0.5], "fraction"),
            100: newIconStyle(this.options.markerPlaceCluster100Svg, [0.5, 0.5], "fraction"),
            1000: newIconStyle(this.options.markerPlaceCluster1000Svg, [0.5, 0.5], "fraction"),
        }
        const mapsPlaces = mapElement.dataset.bettyMapsPlaces
        if (mapsPlaces === undefined) {
            throw new Error(`Element does not have the expected "data-betty-maps-places" attribute.`)
        }
        const placesDataset = JSON.parse(mapsPlaces) as [number, number, string][]
        this.placeDatas = Object.fromEntries(placesDataset.map(items => [items[2], {
            id: items[2],
            latitude: items[0],
            longitude: items[1],
            previewUrlPath: items[2],
        }]))

        this.placeFeatures = {}

        const placeSource = new VectorSource()

        this.placeCluster = new Cluster({
            distance: this.options.clusterMaximumFeatureDistance,
            minDistance: this.options.clusterMinimumClusterDistance,
            source: placeSource,
        })

        const placeLayer = new VectorLayer({
            source: this.placeCluster,
            style: (feature): Style => this.placeLayerStyle(feature),
        })

        const selectedPlaceSource = new VectorSource()

        const selectedPlaceLayer = new VectorLayer({
            source: selectedPlaceSource,
            style: this.placeSelectedStyle,
        })

        this.view = new View({
            constrainResolution: true,
            padding: this.options.viewPadding,
        })

        this.selectedPlace = new SelectedPlace(this, selectedPlaceSource)

        this.map = new OpenLayersMap({
            controls: [],
            interactions: [],
            target: mapElement,
            layers: [
                new TileLayer({
                    source: new OSM({
                        // These are shown using templating instead.
                        attributions: "",
                    }),
                }),
                placeLayer,
                selectedPlaceLayer,
            ],
            view: this.view,
        })
        if (!this.embedded) {
            this.map.addControl(new FullScreen(getTranslationFromShorthandStatic(this.options.fullScreenControlButtonHtml, this.locale), this.map))
            this.map.addControl(new ZoomIn(getTranslationFromShorthandStatic(this.options.zoomInControlButtonHtml, this.locale), this.viewAnimationOptions))
            this.map.addControl(new ZoomOut(getTranslationFromShorthandStatic(this.options.zoomOutControlButtonHtml, this.locale), this.viewAnimationOptions))
            this.map.addControl(this.selectedPlace)
            this.map.addInteraction(new DoubleClickZoom())
            this.map.addInteraction(new DragPan({
                condition: (event): boolean => (event.activePointers !== undefined && event.activePointers.length === 2) || mouseOnly(event) || document.fullscreenElement === this.map.getTargetElement(),
                kinetic,
            }))
            this.map.addInteraction(new DragZoom())
            this.map.addInteraction(new KeyboardPan())
            this.map.addInteraction(new KeyboardZoom())
            this.map.addInteraction(new MouseWheelZoom({
                condition: (event): boolean => platformModifierKeyOnly(event) || document.fullscreenElement === this.map.getTargetElement(),
            }))
            this.map.addInteraction(new PinchZoom())

            this.map.on("pointermove", (event) => {
                document.body.style.cursor = "auto"
                for (const feature of this.map.getFeaturesAtPixel(event.pixel)) {
                    if (feature.get("features")?.length > 1) { // eslint-disable-line @typescript-eslint/no-unsafe-member-access
                        document.body.style.cursor = "zoom-in"
                    }
                    else {
                        document.body.style.cursor = "pointer"
                    }
                }
            })
            this.map.on("click", (event) => {
                void (async (): Promise<void> => {
                    document.body.style.cursor = "auto"
                    for (const feature of this.map.getFeaturesAtPixel(event.pixel)) {
                        const containedFeatures = feature.get("features") as Feature[]
                        if (containedFeatures.length > 1) {
                            this.selectedPlace.unselect()
                            const clusteredPlaces = feature.get("features") as Feature[]
                            const clusteredPlacesCoordinates = clusteredPlaces
                                .map(place => place.getGeometry())
                                .filter(geometry => geometry instanceof Point)
                                .map(point => point.getCoordinates())
                            this.fitView(clusteredPlacesCoordinates)
                        }
                        else {
                            await this.selectedPlace.select(containedFeatures[0].get("placeId") as string)
                        }
                    }
                })()
            })
        }

        const placesCoordinates: number[][] = []
        for (const placeData of Object.values(this.placeDatas)) {
            const placeCoordinates = [placeData.longitude, placeData.latitude]
            placesCoordinates.push(placeCoordinates)
            this.placeFeatures[placeData.id] = new Feature({
                type: "place",
                placeId: placeData.id,
                geometry: new Point(placeCoordinates),
            })
        }

        placeSource.addFeatures(Object.values(this.placeFeatures))

        this.fitView(placesCoordinates)
        new ResizeObserver(() => {
            this.map.updateSize()
        }).observe(mapElement)
    }

    private fitView(coordinates: number[][]): void {
        const mapSize = this.map.getSize()
        if (mapSize === undefined) {
            throw new Error("Map has no size.")
        }
        const extent = boundingExtent(coordinates)
        let resolution = this.view.getResolutionForExtent(extent, [
            mapSize[0] - this.options.viewPadding[0] - this.options.viewPadding[2],
            mapSize[1] - this.options.viewPadding[1] - this.options.viewPadding[3],
        ])
        // Ensure that the resolution does not become so small there is nothing to see.
        if (coordinates.length == 1) {
            resolution = Math.max(10, resolution)
        }
        this.view.animate({
            ...this.viewAnimationOptions,
            resolution: resolution,
            center: getCenter(extent),
        })
    }

    public async initialize(): Promise<void> {
        await BETTY.initialize(this.map.getTargetElement())
        this.map.getTargetElement().classList.add("map-initialized")
    }

    private placeLayerStyle(feature: FeatureLike): Style {
        if (feature.get("features").length > 1) { // eslint-disable-line @typescript-eslint/no-unsafe-member-access
            const places = feature.get("features") as Feature[]
            let scale = 1
            while (scale <= 1000) {
                if (scale * 10 > places.length) {
                    break
                }
                scale *= 10
            }
            return this.placeClusterStyles[scale]
        }
        return this.placeStyle
    }
}

export {
    initializeMap,
    initializeMaps,
    Map,
    MapOptions,
}
