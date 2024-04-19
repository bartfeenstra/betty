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
    cotton_candy: path.resolve(__dirname, 'main.ts')
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
          name: 'cotton_candy',
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
  resolve: {
    extensions: ['', '.ts', '.js', '.*']
  },
  module: {
    rules: [
      {
        test: /\.(s?css)$/,
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
        test: /\.(js|ts)$/,
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
              ],
              '@babel/preset-typescript'
            ],
            cacheDirectory: configuration.cacheDirectory
          }
        }
      }
    ]
  }
}
