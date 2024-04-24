'use strict'

import './trees.css'

import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'

cytoscape.use(dagre)

interface Person {
  childIds: string[]
  id: string,
  label: string,
  parentIds: string[]
  private: boolean,
  url: string,
}

interface EdgeData {
  source: string
  target: string
}

interface Edge {
  data: EdgeData
}

interface Elements {
  nodes: string[]
  edges: Edge[]
}

async function initializeAncestryTrees ():Promise<void> {
  const trees = document.getElementsByClassName('tree')
  for (const tree of trees) {
    await initializeAncestryTree(tree as HTMLElement, tree.dataset.bettyPersonId)
  }
}

async function initializeAncestryTree (tree: HTMLElement, personId: string):Promise<void> {
  const response = await fetch(tree.dataset.bettyPeople)
  const people: Person[] = await response.json()
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
    elements
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
}

function personToNode (person: Person, nodes):void {
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

function parentsToElements (child: Person, elements: Elements, people: Record<string, Person>):void {
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

function childrenToElements (parent: Person, elements: Elements, people: Record<string, Person>):void {
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

document.addEventListener(
  'DOMContentLoaded',
  initializeAncestryTrees, // eslint-disable-line @typescript-eslint/no-misused-promises
)
