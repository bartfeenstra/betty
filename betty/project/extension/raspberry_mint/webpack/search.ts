interface IndexEntry {
    text: string
    result: string
    entityTypeId: string
}

interface Index {
    index: IndexEntry[]
    resultContainerTemplate: string
    resultsContainerTemplate: string
}

class Search {
    private readonly searchModalElement: HTMLElement
    private readonly searchFormElement: HTMLElement
    private readonly searchFormQueryElement: HTMLInputElement
    private readonly searchFormFilterResetElement: HTMLElement
    private readonly resultsContainer: HTMLElement
    private index: Index | undefined
    private readonly filterEntityTypeHtmlIds: Record<string, string>

    public constructor() {
        this.searchModalElement = this.getElementById("nav-search")
        this.searchFormElement = this.getElementById("search-form")
        this.searchFormQueryElement = this.getElementById("search-form-query") as HTMLInputElement
        this.searchFormFilterResetElement = this.getElementById("search-form-filter-reset")
        this.resultsContainer = this.getElementById("search-results-container")

        this.searchModalElement.addEventListener("shown.bs.modal", () => {
            this.searchFormQueryElement.focus()
        })
        this.searchFormElement.addEventListener(
            "submit",
            (e) => {
                void (async (): Promise<void> => {
                    await this.search(this.searchFormQueryElement.value, this.getFilterEntityTypeIds())
                })()
                e.preventDefault()
                e.stopPropagation()
            },
        )
        this.searchFormFilterResetElement.addEventListener("click", () => {
            this.resetFilters()
        })
        const searchFormFilterEntityType = this.searchFormElement.dataset.bettySearchFormFilterEntityType
        if (searchFormFilterEntityType === undefined) {
            throw new Error(`Element does not have the expected "data-betty-search-form-filter-entity-type" attribute.`)
        }
        this.filterEntityTypeHtmlIds = JSON.parse(searchFormFilterEntityType) as Record<string, string>
    }

    private getElementById(id: string): HTMLElement {
        const element = document.getElementById(id)
        if (!element) {
            throw new Error(`Cannot find element with ID #${id}`)
        }
        return element
    }

    private resetFilters(): void {
        this.resetFilterEntityType()
    }

    private getFilterEntityTypeElements(): HTMLInputElement[] {
        return Array.from(this.searchFormElement.querySelectorAll(".search-form-filter-entity-type input"))
    }

    private getFilterEntityTypeIds(): string[] {
        const filterEntityTypeIds: string[] = []
        for (const entityTypeFilterElement of this.getFilterEntityTypeElements()) {
            if (entityTypeFilterElement.checked) {
                filterEntityTypeIds.push(this.filterEntityTypeHtmlIds[entityTypeFilterElement.id])
            }
        }
        return filterEntityTypeIds
    }

    private resetFilterEntityType(): void {
        for (const entityTypeFilterElement of this.getFilterEntityTypeElements()) {
            entityTypeFilterElement.checked = true
        }
    }

    private setSearchEntries(index: Index, entries: IndexEntry[]): void {
        this.resultsContainer.innerHTML = this.renderResults(index, entries)
    }

    private async getIndex(): Promise<Index> {
        if (this.index === undefined) {
            const searchFormIndex = this.searchFormElement.dataset.bettySearchFormIndex
            if (searchFormIndex === undefined) {
                throw new Error(`Element does not have the expected "data-betty-search-form-index" attribute.`)
            }
            const response = await fetch(searchFormIndex)
            this.index = await response.json() as Index
        }
        return this.index
    }

    private async search(query: string, entityTypeIds: string[]): Promise<void> {
        const queryParts = query.toLowerCase().split(/\s/).filter(queryPart => queryPart.trim().length)
        const index = await this.getIndex()
        if (queryParts.length) {
            this.setSearchEntries(index, index.index.filter(entry => this.match(queryParts, entityTypeIds, entry)))
        }
        else {
            this.setSearchEntries(index, [])
        }
    }

    private match(queryParts: string[], entityTypeIds: string[], entry: IndexEntry): boolean {
        if (!entityTypeIds.includes(entry.entityTypeId)) {
            return false
        }
        for (const queryPart of queryParts) {
            if (!entry.text.includes(queryPart)) {
                return false
            }
        }
        return true
    }

    private renderResults(index: Index, entries: IndexEntry[]): string {
        return index.resultsContainerTemplate
            .replace("{{{ betty-search-results }}}", entries.map(entry => this.renderResult(index, entry)).join(""))
            .replace("{{{ betty-search-results-count }}}", entries.length.toString())
    }

    private renderResult(index: Index, entry: IndexEntry): string {
        return index.resultContainerTemplate
            .replace("{{{ betty-search-result }}}", entry.result)
    }
}

export {
    Search,
}
