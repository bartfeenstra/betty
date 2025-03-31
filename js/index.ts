type Initializer = (element: Element) => Promise<void>
type Finalizer = (element: Element) => Promise<void>

class Betty {
    private readonly initializers: Initializer[]
    private readonly finalizers: Finalizer[]

    public constructor() {
        this.initializers = []
        this.finalizers = []
    }

    public async addInitializer(initializer: Initializer): Promise<void> {
        if (this.initializers.includes(initializer)) {
            return
        }
        this.initializers.push(initializer)
        await initializer(document.body)
    }

    public async initialize(element: Element): Promise<void> {
        for (const initializer of this.initializers) {
            await initializer(element)
        }
    }

    public addFinalizer(finalizer: Finalizer): void {
        if (this.finalizers.includes(finalizer)) {
            return
        }
        this.finalizers.push(finalizer)
    }

    public async finalize(element: Element): Promise<void> {
        for (const finalizer of this.finalizers) {
            await finalizer(element)
        }
    }
}

export {
    Betty,
}
