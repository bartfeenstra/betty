'use strict'

import eslint from '@eslint/js'
import stylistic from '@stylistic/eslint-plugin'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default [
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
            'betty/project/extension/http_api_doc/webpack/**',
            'betty/project/extension/maps/webpack/**',
            'betty/project/extension/raspberry_mint/webpack/**',
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
    eslint.configs.recommended,
    {
        languageOptions: {
            parserOptions: {
                ecmaVersion: 2022,
            },
        },
    },
    stylistic.configs.customize({
        indent: 4,
        quotes: 'double',
    }),

    // Generic TypeScript.
    ...[
        ...tseslint.configs.strictTypeChecked,
        {
            languageOptions: {
                parserOptions: {
                    project: [
                        'tsconfig.json',
                    ],
                },
            },
            rules: {
                '@typescript-eslint/explicit-function-return-type': 'error',
                '@typescript-eslint/explicit-member-accessibility': 'error',
                '@typescript-eslint/explicit-module-boundary-types': 'error'
            },
        },
    ].map(config => ({
        files: [
            '**/*.ts',
        ],
        ...config,
    })),
]
