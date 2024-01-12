'use strict'

const { CleanWebpackPlugin } = require('clean-webpack-plugin')
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin')
const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const configuration = require('./webpack.config.json')
const webpack = require('webpack')

/**
 * Collect the scripts needed for all entrypoints, and build a loader.
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
const entryScriptsMap = ${JSON.stringify(scripts)}
const importedScripts = []
const entryNames = document.getElementById('webpack-entry-loader').dataset.webpackEntryLoader.split(':')
const entryScripts = new Set(...entryNames.reduce(
  (accumulatedEntryScripts, entryName) => [...accumulatedEntryScripts, entryScriptsMap[entryName]],
  [],
))
const importPromises = []
for (const entryScript of entryScripts) {
  importPromises.push(import(entryScript))
}
Promise.allSettled(importPromises).then(modules => {})
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
    path: path.resolve(__dirname, 'build'),
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
        // This make for easy importing.
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
    new EntryScriptCollector(),
    new CleanWebpackPlugin(),
    new MiniCssExtractPlugin({
      filename: 'css/[name].css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              cacheDirectory: configuration.cacheDirectory,
              presets: [
                [
                  '@babel/preset-env', {
                    debug: configuration.debug,
                    modules: false,
                    useBuiltIns: 'usage',
                    corejs: 3
                  }
                ]
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
              url: false
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

module.exports = webpackConfiguration
