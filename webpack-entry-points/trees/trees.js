"use strict"

import cytoscape from "cytoscape"
import dagre from "cytoscape-dagre"

cytoscape.use(dagre)

async function initializeAncestryTrees(element, treeOptions) {
    if (!element) {
        element = document
    }
    const trees = element.getElementsByClassName("tree-content")
    await Promise.allSettled(Array.from(trees).map(tree => initializeAncestryTree(tree, treeOptions, tree.dataset.bettyPerson)))
}

async function initializeAncestryTree(tree, treeOptions, personId) {
    const response = await fetch(tree.dataset.bettyPeople)
    const people = await response.json()
    const elements = {
        nodes: [],
        edges: [],
    }
    const person = people[personId]
    personToNode(person, elements.nodes)
    parentsToElements(person, elements, people)
    childrenToElements(person, elements, people)
    const cy = cytoscape({
        container: tree,
        layout: {
            name: "dagre",
        },
        wheelSensitivity: 0.25,
        style: [
            {
                selector: "node",
                style: {
                    "content": "data(label)",
                    "shape": "round-rectangle",
                    "text-valign": "center",
                    "text-halign": "center",
                    "background-color": treeOptions.nodeBackgroundColor,
                    "width": "label",
                    "height": "label",
                    "padding": "9px",
                },
            },
            {
                selector: "node.public",
                style: {
                    color: treeOptions.nodeColor,
                },
            },
            {
                selector: "node.public.hover",
                style: {
                    color: treeOptions.nodeHoverColor,
                },
            },
            {
                selector: "edge",
                style: {
                    "curve-style": "taxi",
                    "taxi-direction": "downward",
                    "width": 4,
                    "target-arrow-shape": "triangle",
                    "line-color": treeOptions.edgeColor,
                    "target-arrow-color": treeOptions.edgeColor,
                },
            },
        ],
        elements,
    })
    cy.zoom({
        level: 1,
        position: cy.getElementById(personId).position(),
    })
    cy.on("mouseover", "node.public", (event) => {
        event.target.addClass("hover")
    })
    cy.on("mouseout", "node.public", (event) => {
        event.target.removeClass("hover")
    })
    cy.on("tap", "node.public", (event) => {
        window.location = event.target.data().url
    })
}

function personToNode(person, nodes) {
    nodes.push({
        data: {
            id: person.id,
            label: person.label,
            url: person.url,
        },
        selectable: false,
        grabbable: false,
        pannable: true,
        classes: person.private ? [] : ["public"],
    })
}

function parentsToElements(child, elements, people) {
    for (const parentId of child.parentIds) {
        const parent = people[parentId]
        elements.edges.push({
            data: {
                source: parent.id,
                target: child.id,
            },
        })
        personToNode(parent, elements.nodes)
        parentsToElements(parent, elements, people)
    }
}

function childrenToElements(parent, elements, people) {
    for (const childId of parent.childIds) {
        const child = people[childId]
        elements.edges.push({
            data: {
                source: parent.id,
                target: child.id,
            },
        })
        personToNode(child, elements.nodes)
        childrenToElements(child, elements, people)
    }
}

export {
    initializeAncestryTrees,
}
