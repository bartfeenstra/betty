'use strict'

import treesStyle from './trees.css' // eslint-disable-line no-unused-vars

import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'

cytoscape.use(dagre)

function initializeAncestryTrees () {
  const trees = document.getElementsByClassName('tree')
  for (const tree of trees) {
    initializeAncestryTree(tree, tree.dataset.bettyPersonId)
  }
}

function initializeAncestryTree (tree, personId) {
  fetch(tree.dataset.bettyPeople)
    .then((response) => response.json())
    .then((people) => {
      const elements = {
        nodes: [],
        edges: []
      }
      const person = people[personId]
      personToNode(person, elements.nodes)
      parentsToElements(person, elements, people)
      childrenToElements(person, elements, people)
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
              content: 'data(label)',
              shape: 'round-rectangle',
              'text-valign': 'center',
              'text-halign': 'center',
              'background-color': '#eee',
              width: 'label',
              height: 'label',
              padding: '9px'
            }
          },
          {
            selector: 'node.public',
            style: {
              color: '#149988'
            }
          },
          {
            selector: 'node.public.hover',
            style: {
              color: '#2a615a'
            }
          },
          {
            selector: 'edge',
            style: {
              'curve-style': 'taxi',
              'taxi-direction': 'downward',
              width: 4,
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
      cy.on('mouseover', 'node.public', (event) => {
        event.target.addClass('hover')
      })
      cy.on('mouseout', 'node.public', (event) => {
        event.target.removeClass('hover')
      })
      cy.on('tap', 'node.public', (event) => {
        window.location = event.target.data().url
      })
    })
}

function personToNode (person, nodes) {
  nodes.push({
    data: {
      id: person.id,
      label: person.label,
      url: person.url
    },
    selectable: false,
    grabbable: false,
    pannable: true,
    classes: person.private ? [] : ['public']
  })
}

function parentsToElements (child, elements, people) {
  for (const parentId of child.parentIds) {
    const parent = people[parentId]
    elements.edges.push({
      data: {
        source: parent.id,
        target: child.id
      }
    })
    personToNode(parent, elements.nodes)
    parentsToElements(parent, elements, people)
  }
}

function childrenToElements (parent, elements, people) {
  for (const childId of parent.childIds) {
    const child = people[childId]
    elements.edges.push({
      data: {
        source: parent.id,
        target: child.id
      }
    })
    personToNode(child, elements.nodes)
    childrenToElements(child, elements, people)
  }
}

document.addEventListener('DOMContentLoaded', initializeAncestryTrees)
