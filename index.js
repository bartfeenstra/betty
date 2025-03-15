class Betty {
    constructor() {
        this.initializers = [];
        this.finalizers = [];
    }
    async addInitializer(initializer) {
        this.initializers.push(initializer);
        await initializer(document.body);
    }
    async initialize(element) {
        for (const initializer of this.initializers) {
            await initializer(element);
        }
    }
    addFinalizer(finalizer) {
        this.finalizers.push(finalizer);
    }
    async finalize(element) {
        for (const finalizer of this.finalizers) {
            await finalizer(element);
        }
    }
}
export { Betty, };
