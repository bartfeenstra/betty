'use strict'

import eslint from '@eslint/js'
import stylistic from '@stylistic/eslint-plugin'
import globals from 'globals'
import playwright from 'eslint-plugin-playwright'
import tseslint from 'typescript-eslint'

const typescriptFiles = [
    '**/*.ts',
]

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

    // Playwright tests.
    {
        files: [
            'playwright/tests/**',
        ],
        ...playwright.configs['flat/recommended'],

    },

    // Generic EcmaScript.
  {
    plugins: {
      '@stylistic': stylistic,
    },
    rules: {
      '@stylistic/function-call-spacing': ['error', 'never'],
      '@stylistic/object-curly-newline': 'error',
      '@stylistic/object-property-newline': ['error', {
          'allowAllPropertiesOnSameLine': true,
      }],
      '@stylistic/one-var-declaration-per-line': ['error', 'always'],
      '@stylistic/semi': ['error', 'never'],
    }
  },
    eslint.configs.recommended,
    {
        languageOptions: {
            parserOptions: {
                ecmaVersion: 2022,
            },
        },
    },

    // Generic TypeScript.
    ...[
        ...tseslint.configs.strictTypeChecked,
        ...tseslint.configs.stylisticTypeChecked,
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
        files: typescriptFiles,
        ...config,
    })),
]
