/// <reference types="cypress" />

context('ReDoc', () => {
  it('load ReDoc', () => {
    cy.task('generate', {
      extensions: {
        'betty.extension.HttpApiDoc': {}
      }
    })
      .then((rootPath) => {
        cy.visit(rootPath + '/api/index.html')
      })
  })
})
