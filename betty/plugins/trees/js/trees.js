'use strict'

import treesStyle from './trees.css' // eslint-disable-line no-unused-vars

import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import ancestry from './ancestry.json'

cytoscape.use(dagre)

function initializeAncestryTrees () {
  const trees = document.getElementsByClassName('tree')
  for (let tree of trees) {
    initializeAncestryTree(tree, tree.dataset.bettyPersonId)
  }
}

function initializeAncestryTree (container, personId) {
  let elements = {
    nodes: [],
    edges: []
  }
  personToElements(ancestry.people[personId], elements)
  const cy = cytoscape({
    container: document.getElementsByClassName('tree')[0],
    layout: {
      name: 'dagre'
    },
    wheelSensitivity: 0.25,
    style: [
      {
        selector: 'node',
        style: {
          'content': 'data(label)',
          'shape': 'round-rectangle',
          'text-valign': 'center',
          'text-halign': 'center',
          'background-color': '#eee',
          'width': 'label',
          'height': 'label',
          'padding': '9px'
        }
      },
      {
        selector: 'edge',
        style: {
          'curve-style': 'taxi',
          'taxi-direction': 'downward',
          'width': 4,
          'target-arrow-shape': 'triangle',
          'line-color': '#777',
          'target-arrow-color': '#777'
        }
      }
    ],
    elements: elements
  })
  cy.zoom({
    level: 1,
    position: cy.getElementById(personId).position()
  })
}

function personToElements (person, elements) {
  personToNode(person, elements.nodes)
  parentsToElements(person, elements)
  childrenToElements(person, elements)
}

function personToNode (person, nodes) {
  const label = person.private ? 'private' : person.family_name + ', ' + person.individual_name
  nodes.push({
    data: {
      id: person.id,
      label: label
    },
    selectable: false,
    grabbable: false,
    pannable: true
  })
}

function parentsToElements (child, elements) {
  for (let parentId of child.parent_ids) {
    let parent = ancestry.people[parentId]
    elements.edges.push({
      data: {
        source: parent.id,
        target: child.id
      }
    })
    personToNode(parent, elements.nodes)
    parentsToElements(parent, elements)
  }
}

function childrenToElements (parent, elements) {
  for (let childId of parent.child_ids) {
    let child = ancestry.people[childId]
    elements.edges.push({
      data: {
        source: parent.id,
        target: child.id
      }
    })
    personToNode(child, elements.nodes)
    childrenToElements(child, elements)
  }
}

export {
  initializeAncestryTrees as betty
}
