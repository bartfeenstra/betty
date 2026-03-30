import SwaggerUI from "swagger-ui"

document.querySelectorAll("[data-betty-openapi-url]").forEach((element) => {
    SwaggerUI({
        url: element.dataset.bettyOpenapiUrl,
        dom_id: `#${element.id}`,
    })
})
