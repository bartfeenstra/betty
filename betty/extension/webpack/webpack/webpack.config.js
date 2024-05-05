'use strict'

import { CleanWebpackPlugin } from 'clean-webpack-plugin'
import CopyWebpackPlugin from 'copy-webpack-plugin'
import CssMinimizerPlugin from 'css-minimizer-webpack-plugin'
import MiniCssExtractPlugin from 'mini-css-extract-plugin'
import path from 'path'
import { readFile } from 'node:fs/promises'
import TerserPlugin from 'terser-webpack-plugin'
import url from 'node:url'
import webpack from 'webpack'

const __dirname = url.fileURLToPath(new URL('.', import.meta.url))
const configuration = JSON.parse(await readFile('./webpack.config.json'))

/**
 * Collect the scripts needed for all entrypoints, and build a loader.
 *
 * We do this, because page generation and the Webpack build take place concurrently for performance reasons.
 * When rendered, pages declare the Webpack extension entrypoints they need.
 * Using this Webpack plugin, we build a map of all scripts needed per entrypoint,
 * as well as a loader that is run on each page. The loader then imports the
 * scripts needed for the entrypoints declared on the page.
 */
class EntryScriptCollector {
  apply (compiler) {
    compiler.hooks.initialize.tap('ChunkCollector', () => {
      compiler.hooks.thisCompilation.tap(
        'ChunkCollector',
        (compilation) => {
          compilation.hooks.processAssets.tapAsync(
            {
              name: 'ChunkCollector',
              stage: compiler.webpack.Compilation.PROCESS_ASSETS_STAGE_OPTIMIZE_INLINE
            },
            (_, callback) => {
              const extensionRegexp = /\.(js|mjs)(\?|$)/
              const scripts = {}
              for (const entryName of Object.keys(configuration.entry)) {
                scripts[entryName] = compilation.entrypoints
                  .get(entryName)
                  .getFiles()
                  .filter(entryFile => extensionRegexp.test(entryFile))
                  .map(entryFile => `/${entryFile}`)
              }

              const webpackEntryLoader = `
(async () => {
    const entryScriptsMap = ${JSON.stringify(scripts)}
    const entryNames = document.getElementById('webpack-entry-loader').dataset.webpackEntryLoader.split(':')
    const entryScripts = new Set(entryNames.reduce(
        (accumulatedEntryScripts, entryName) => [...accumulatedEntryScripts, ...entryScriptsMap[entryName]],
        [],
    ))
    await Promise.allSettled([...entryScripts].map(async (entryScript) => await import(entryScript)))
})()
`
              compilation.emitAsset(
                path.join('js', 'webpack-entry-loader.js'),
                new webpack.sources.RawSource(webpackEntryLoader)
              )
              return callback()
            }
          )
        }
      )
    })
  }
}

const webpackConfiguration = {
  mode: configuration.debug ? 'development' : 'production',
  devtool: configuration.debug ? 'eval-source-map' : false,
  entry: configuration.entry,
  output: {
    path: path.resolve(__dirname, configuration.buildDirectoryPath),
    filename: 'js/[name].js'
  },
  optimization: {
    concatenateModules: true,
    minimize: !configuration.debug,
    minimizer: [
      new CssMinimizerPlugin(),
      new TerserPlugin({
        extractComments: false,
        terserOptions: {
          output: {
            comments: false
          }
        }
      })
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // The resulting CSS files are one per entrypoint, and a single vendor.css.
        // This makes for easy and unconditional importing.
        vendorCss: {
          test: /[\\/]node_modules[\\/].+?\.css$/,
          name: 'vendor',
          priority: -10
        },
        vendorJs: {
          test: /[\\/]node_modules[\\/].+?\.js$/,
          priority: -10
        }
      }
    },
    runtimeChunk: 'single'
  },
  plugins: [
    new CleanWebpackPlugin(),
    new CopyWebpackPlugin({
      patterns: [
        // The HttpApiDoc extension does not have a Webpack build as such (yet), but simply
        // requires a single dependency distribution asset verbatim.
        {
          from: path.join('node_modules','redoc', 'bundles', 'redoc.standalone.js'),
          to: 'js/http-api-doc.js',
          noErrorOnMissing: true,
        },
      ],
    }),
    new EntryScriptCollector(),
    new MiniCssExtractPlugin({
      filename: 'css/[name].css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.(js|ts)$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              cacheDirectory: path.resolve(__dirname, 'cache'),
              presets: [
                [
                  '@babel/preset-env', {
                    debug: configuration.debug,
                    modules: false,
                    useBuiltIns: 'usage',
                    corejs: 3
                  },
                ],
                '@babel/preset-typescript',
              ]
            }
          }
        ]
      },
      {
        test: /\.s?css$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              publicPath: '/'
            }
          },
          {
            loader: 'css-loader',
            options: {
              url: {
                // Betty's own assets are generated through the assets file system,
                // so we use Webpack for vendor assets only.
                filter: (url, resourcePath) => resourcePath.includes('/node_modules/'),
              }
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: () => [
                  require('autoprefixer')
                ]
              }
            }
          },
          {
            loader: 'sass-loader'
          }
        ]
      },
      {
        test: /.*\.png|gif|jpg|jpeg|svg/,
        type: 'asset/resource',
        generator: {
          filename: 'images/[hash][ext]'
        }
      }
    ]
  }
}

export default webpackConfiguration
