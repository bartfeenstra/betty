/// <reference types="cypress" />

const path = require('path')

context('Search', () => {
  it('search, find, and navigate to a resource', () => {
    return cy.task('generate', {
      extensions: {
        'betty.extension.CottonCandy': {},
        'betty.extension.Gramps': {
          enabled: true,
          configuration: {
            family_trees: [
              {
                file: path.join('..', 'fixtures', 'gramps.xml')
              }
            ]
          }
        }
      }
    })
      .then((rootPath) => {
        cy.visit(rootPath)
        cy.get('#search-query')
          .type('Janet')
          .type('{downarrow}')
        cy.get(':focus')
          .click()

        cy.location('pathname')
          .should('eq', rootPath + '/person/I0001/index.html')
      })
  })
})
