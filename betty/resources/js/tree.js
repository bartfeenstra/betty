'use strict'

import * as d3 from 'd3'
import ancestry from './ancestry.json'

let treeCount = 0

function initializeAncestryTrees() {
    const ancestryTrees = document.getElementsByClassName('tree')
    for (let ancestryTree of ancestryTrees) {
        initializeAncestryTree(ancestryTree)
    }
}

function initializeAncestryTree(ancestryTree) {
    const treeArea = ancestryTree
    treeCount++
    treeArea.id = `tree-${treeCount}`

    const data = Object.values(ancestry.people)

    // const tree = d3.select(`#${treeArea.id}`)
    // tree.selectAll('p')
    //     .data(data)
    //     .enter()
    //     .append('p')
    //     .text((d) => `${d.family_name}, ${d.individual_name}`)
    //
    // const clusterRoot = d3.stratify()
    // .id((d) => d.id)
    // .parentId((d) => )
    // (data);
    //
    // // @todo Use I0000 as the root while testing. Clusters are trees, so we must always use a specific person as the starting point.
    // const cluster = d3.cluster()



  var g = new dagreD3.graphlib.Graph()
  	.setGraph({}).setDefaultEdgeLabel(function() { return {}; });

  g.setNode("pp1",    { label: "PP1", rank: "same_pp" });
  g.setNode("pp2",    { label: "PP2", rank: "same_pp" });
  g.setNode("pp3",    { label: "PP3", rank: "same_pp" });
  g.setNode("pp4",    { label: "PP4", rank: "same_pp" });
  g.setNode("p1",    { label: "P1", rank: "same_p" });
  g.setNode("p2",  { label: "P2", rank: "same_p" });
  g.setNode("p3",    { label: "P3", rank: "same_p" });
  g.setNode("c1",      { label: "C1", rank: "same_c" });
  g.setNode("c2",      { label: "C2", rank: "same_c" });

  g.setEdge( "pp1",   "p1");
  g.setEdge( "pp2",   "p1");
  g.setEdge( "pp3",   "p2");
  g.setEdge( "pp4",   "p2");
  g.setEdge( "p2",     "c2");
  g.setEdge( "p1", "c2");
  g.setEdge( "p1", "c1");
  g.setEdge( "p3",     "c1");

  var renderer = new dagreD3.render();
  //renderer.edgeInterpolate('linear');
  renderer(d3.select("svg g"), g);
}

export {initializeAncestryTrees}
