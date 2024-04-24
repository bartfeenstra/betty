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

    // Betty extensions using the _Npm extension.
    {
        files: [
            'betty/extension/cotton_candy/assets/betty.extension.npm._Npm/src/**',
            'betty/extension/maps/assets/betty.extension.npm._Npm/src/**',
            'betty/extension/trees/assets/betty.extension.npm._Npm/src/**',
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
