import js from "@eslint/js"
import globals from "globals"
import tseslint from "typescript-eslint"
import { defineConfig } from "eslint/config"

import stylistic from "@stylistic/eslint-plugin"

export default defineConfig([
    // Webpack configuration files.
    {
        files: [
            '**/webpack.config.js',
        ],
        languageOptions: {
            globals: {
                ...globals.node,
            },
        },
    },

    // The Webpack extension and other extensions using it.
    {
        files: [
            'betty/project/extension/cotton_candy/webpack/**',
            'betty/project/extension/http_api_doc/webpack/**',
            'betty/project/extension/maps/webpack/**',
            'betty/project/extension/trees/webpack/**',
            'betty/project/extension/webpack/webpack/**',
        ],
        languageOptions: {
            globals: {
                ...globals.browser,
            },
        },
    },

    // Generic EcmaScript.
    js.configs.recommended,
    stylistic.configs.customize({
        indent: 4,
        quotes: "double",
    }),

    // Generic TypeScript.
    {
        files: [
            "**/*.ts",
        ],
        extends: [tseslint.configs.strictTypeChecked],
        languageOptions: {
            parserOptions: {
                project: [
                    "tsconfig.json",
                ],
            },
        },
        rules: {
            "@typescript-eslint/explicit-function-return-type": "error",
            "@typescript-eslint/explicit-member-accessibility": "error",
            "@typescript-eslint/explicit-module-boundary-types": "error",
        },
    },
])
