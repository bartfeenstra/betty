'use strict'

const { CleanWebpackPlugin } = require('clean-webpack-plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const path = require('path')
const configuration = require('./webpack.config.json')

module.exports = {
  mode: configuration.mode,
  entry: {
    maps: path.resolve(__dirname, 'maps.js')
  },
  output: {
    path: path.resolve(__dirname, '..', 'output'),
    filename: '[name].js'
  },
  optimization: {
    minimize: configuration.minimize,
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
        test: /.*\.png$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: 'images/[hash].[ext]',
              publicPath: '/'
            }
          }
        ]
      }
    ]
  }
}
