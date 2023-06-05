/// <reference types="cypress" />

context('ReDoc', () => {
  it('load ReDoc', () => {
    cy.task('generate', {
      extensions: {
        'betty.http_api_doc.HttpApiDoc': {}
      }
    })
      .then((rootPath) => {
        cy.visit(rootPath + '/api/index.html')
      })
  })
})
