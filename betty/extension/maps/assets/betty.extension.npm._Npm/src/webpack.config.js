'use strict'

import { CleanWebpackPlugin } from 'clean-webpack-plugin'
import MiniCssExtractPlugin from 'mini-css-extract-plugin'
import path from 'path'
import { readFile } from 'node:fs/promises'
import url from 'node:url'

const __dirname = url.fileURLToPath(new URL('.', import.meta.url))
const configuration = JSON.parse(await readFile('./webpack.config.json'))

export default {
  mode: configuration.debug ? 'development' : 'production',
  entry: {
    maps: path.resolve(__dirname, 'maps.js')
  },
  output: {
    path: path.resolve(__dirname, 'webpack-build'),
    filename: '[name].js'
  },
  optimization: {
    minimize: !configuration.debug,
    splitChunks: {
      cacheGroups: {
        styles: {
          name: 'maps',
          // Group all CSS files into a single file.
          test: /\.css$/,
          chunks: 'all',
          enforce: true
        }
      }
    }
  },
  plugins: [
    new CleanWebpackPlugin(),
    new MiniCssExtractPlugin({
      filename: '[name].css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              publicPath: '/'
            }
          },
          {
            loader: 'css-loader'
          }
        ]
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              [
                '@babel/preset-env', {
                  debug: configuration.debug,
                  useBuiltIns: 'usage',
                  corejs: 3
                }
              ]
            ],
            cacheDirectory: configuration.cacheDirectory
          }
        }
      },
      // Bundle Leaflet images.
      {
        test: /.*\.png|svg$/,
        type: 'asset/resource',
        generator: {
          filename: 'images/[hash][ext]'
        }
      }
    ]
  }
}
