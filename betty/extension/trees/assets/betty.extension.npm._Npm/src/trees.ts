'use strict'

import './trees.css'

import cytoscape, {CytoscapeOptions, ElementsDefinition, NodeDataDefinition} from 'cytoscape'
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

function initializeAncestryTrees () :void {
  const trees = document.getElementsByClassName('tree')
  Array.from(trees).forEach(async (tree: HTMLElement) => {
    await initializeAncestryTree(tree, tree.dataset.bettyPersonId)
  })
}

async function initializeAncestryTree (tree: HTMLElement, personId: string):Promise<void> {
  const response = await fetch(tree.dataset.bettyPeople)
  const people = await response.json() as Record<string, Person>
  const elements: ElementsDefinition = {
    nodes: [],
    edges: []
  }
  const person = people[personId]
  personToNode(person, elements.nodes)
  parentsToElements(person, elements, people)
  childrenToElements(person, elements, people)
  const cytoscapeOptions: CytoscapeOptions = {
    container: document.getElementsByClassName('tree')[0] as HTMLElement,
    layout: {
      name: 'dagre'
    },
    style: [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          // shape: 'round-rectangle',
          // // 'text-valign': 'center',
          // // 'text-halign': 'center',
          // 'background-color': '#eee',
          // width: 'label',
          // height: 'label',
          // // padding: '9px'
        }
      },
      // {
      //   selector: 'node.public',
      //   style: {
      //     color: '#149988'
      //   }
      // },
      // {
      //   selector: 'node.public.hover',
      //   style: {
      //     color: '#2a615a'
      //   }
      // },
      // {
      //   selector: 'edge',
      //   style: {
      //     'curve-style': 'taxi',
      //     'taxi-direction': 'downward',
      //     width: 4,
      //     'target-arrow-shape': 'triangle',
      //     'line-color': '#777',
      //     'target-arrow-color': '#777'
      //   }
      // }
    ],
    elements
  }
  const cy = cytoscape(cytoscapeOptions)
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

function personToNode (person: Person, nodes: NodeDataDefinition[]):void {
  nodes.push({
    data: {
      id: person.id,
      label: person.label,
      url: person.url,
    },
    selectable: false,
    grabbable: false,
    pannable: true,
    classes: person.private ? [] : ['public'],
  })
}

function parentsToElements (child: Person, elements: ElementsDefinition, people: Record<string, Person>):void {
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

function childrenToElements (parent: Person, elements: ElementsDefinition, people: Record<string, Person>):void {
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

document.addEventListener(
  'DOMContentLoaded',
  initializeAncestryTrees, // eslint-disable-line @typescript-eslint/no-misused-promises
)
