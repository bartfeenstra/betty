/// <reference types="cypress" />

context('Search', () => {
  it('search, find, and navigate to a resource', () => {
    cy.fixture('gramps.xml')
      .then(gramps => {
        return cy.task('generate', [{}, gramps])
      })
      .then((rootPath) => {
        cy.visit(rootPath)
        cy.get('#search-query')
          .type('Janet', {
            delay: 100
          })
          .type('{downarrow}')
        cy.get(':focus')
          .click()

        cy.location('pathname')
          .should('eq', rootPath + '/person/I0001/index.html')
      })
  })
})
