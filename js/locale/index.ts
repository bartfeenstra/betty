function getLocale(): string {
    const locale = document.documentElement.getAttribute("lang")
    if (locale === null) {
        throw new Error("This document has no global `lang` attribute.")
    }
    return locale
}

export {
    getLocale,
}
