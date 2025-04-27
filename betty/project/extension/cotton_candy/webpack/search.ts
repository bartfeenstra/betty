interface IndexEntry {
    text: string
    result: string
}

interface Index {
    index: IndexEntry[]
    resultContainerTemplate: string
    resultsContainerTemplate: string
}

class Search {
    private readonly hideSearchKeys = ["Escape"]
    private readonly nextResultKeys = ["ArrowDown"]
    private readonly previousResultKeys = ["ArrowUp"]
    private readonly search: HTMLElement
    private readonly form: HTMLElement
    private readonly queryElement: HTMLInputElement
    private readonly resultsContainer: HTMLElement
    private documentY: number | undefined
    private index: Index | undefined

    public constructor() {
        this.search = this.getElementById("search")
        this.form = this.search.getElementsByTagName("form").item(0) as HTMLElement
        this.queryElement = this.getElementById("search-query") as HTMLInputElement
        this.resultsContainer = this.getElementById("search-results-container")
    }

    private getElementById(id: string): HTMLElement {
        const element = document.getElementById(id)
        if (!element) {
            throw new Error(`Cannot find element with ID #${id}`)
        }
        return element
    }

    public initialize(): void {
    // Prevent default form submission behaviors, such as HTTP requests.
        this.form.addEventListener("submit", (e) => {
            e.preventDefault()
            e.stopPropagation()
        })

        this.queryElement.addEventListener(
            "keyup",
            () => {
                void (async (): Promise<void> => {
                    await this.perform(this.queryElement.value)
                })()
            },
        )

        // Allow keyboard navigation through the results.
        this.queryElement.addEventListener("keydown", (e) => {
            this.navigateResults(e.key)
        })
        // Allow navigation into and out of the search.

        this.resultsContainer.addEventListener("keydown", (e) => {
            this.navigateResults(e.key)
        })
        this.queryElement.addEventListener("focus", () => {
            this.showSearchResults()
        })
        this.search.getElementsByClassName("overlay-close")[0].addEventListener("mouseup", () => {
            this.hideSearchResults()
        })
        document.addEventListener("keydown", (e) => {
            if (this.hideSearchKeys.includes(e.key)) {
                this.hideSearchResults()
            }
        })
    }

    private navigateResults(keyCode: string): void {
        const activeElement = document.activeElement
        if (!activeElement) {
            return
        }
        if (this.previousResultKeys.includes(keyCode)) {
            // If the focus lies on the query input element, do nothing, because there are no previous search results.
            if (activeElement === this.queryElement) {
                return
            }

            if (activeElement.classList.contains("search-result-target")) {
                // If the focus lies on a search result, focus on the previous search result if there is one.
                const searchResultContainer = activeElement.closest(".search-result")
                if (searchResultContainer) {
                    const previousSearchResultContainer = searchResultContainer.previousElementSibling
                    if (previousSearchResultContainer) {
                        const previousSearchResultTarget = previousSearchResultContainer.querySelector<HTMLElement>(".search-result-target")
                        if (previousSearchResultTarget) {
                            previousSearchResultTarget.focus()
                        }
                        return
                    }
                }

                // If no previous search result exists, focus on the query input element.
                this.queryElement.focus()
            }
        }
        else if (this.nextResultKeys.includes(keyCode)) {
            // If the focus lies on the query input element, focus on the first search result.
            if (activeElement === this.queryElement) {
                const resultTargets = this.resultsContainer.getElementsByClassName("search-result-target") as HTMLCollectionOf<HTMLElement>
                if (resultTargets.length) {
                    resultTargets[0].focus()
                }
                return
            }
            // If the focus lies on a search result, focus on the next search result if there is one.
            if (activeElement.classList.contains("search-result-target")) {
                const nextSearchResultContainer = activeElement.closest(".search-result")?.nextElementSibling
                if (nextSearchResultContainer) {
                    const nextSearchResultTarget = nextSearchResultContainer.querySelector<HTMLElement>(".search-result-target")
                    if (nextSearchResultTarget) {
                        nextSearchResultTarget.focus()
                    }
                }
            }
        }
    }

    private setSearchEntries(index: Index, entries: IndexEntry[]): void {
        this.resultsContainer.innerHTML = this.renderResults(index, entries)
        this.resultsContainer.scrollTop = 0
    }

    private showSearchResults(): void {
        if (!this.documentY) {
            this.documentY = window.scrollY
        }
        this.search.classList.add("overlay")
        document.body.classList.add("has-overlay")
        if (!this.search.contains(document.activeElement)) {
            this.queryElement.focus()
        }
    }

    private hideSearchResults(): void {
        const activeElement = document.activeElement
        if (activeElement instanceof HTMLElement && this.search.contains(activeElement)) {
            activeElement.blur()
        }
        this.search.classList.remove("overlay")
        document.body.classList.remove("has-overlay")
        if (this.documentY) {
            window.scrollTo({
                top: this.documentY,
            })
            this.documentY = undefined
        }
    }

    private async getIndex(): Promise<Index> {
        if (this.index === undefined) {
            const searchIndex = this.search.dataset.bettySearchIndex
            if (searchIndex === undefined) {
                throw new Error(`Element does not have the expected "data-betty-search-index" attribute.`)
            }
            const response = await fetch(searchIndex)
            this.index = await response.json() as Index
        }
        return this.index
    }

    private async perform(query: string): Promise<void> {
        const index = await this.getIndex()
        this.setSearchEntries(index, index.index.filter(entry => this.match(query, entry.text)))
    }

    private match(query: string, haystack: string): boolean {
        const queryParts = query.toLowerCase().split(/\s/)
        for (const queryPart of queryParts) {
            if (!haystack.includes(queryPart)) {
                return false
            }
        }
        return true
    }

    private renderResults(index: Index, entries: IndexEntry[]): string {
        return index.resultsContainerTemplate
            .replace("{{{ betty-search-results }}}", entries.map(entry => this.renderResult(index, entry)).join(""))
    }

    private renderResult(index: Index, entry: IndexEntry): string {
        return index.resultContainerTemplate
            .replace("{{{ betty-search-result }}}", entry.result)
    }
}

export {
    Search,
}
