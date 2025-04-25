type StaticTranslations = Record<string, string>
type ShorthandStaticTranslations = StaticTranslations | string

function getTranslationFromShorthandStatic(translations: ShorthandStaticTranslations, locale: string): string {
    if (typeof translations === "string") {
        return translations
    }
    let translation = translations[locale]
    if (translation !== undefined) { // eslint-disable-line @typescript-eslint/no-unnecessary-condition
        return translation
    }
    translation = Object.values(translations)[0]
    if (translation !== undefined) { // eslint-disable-line @typescript-eslint/no-unnecessary-condition
        return translation
    }
    throw new Error("No translations were given.")
}

export {
    getTranslationFromShorthandStatic,
    ShorthandStaticTranslations,
    StaticTranslations,
}
