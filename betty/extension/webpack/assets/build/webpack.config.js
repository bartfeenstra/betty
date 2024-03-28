'use strict'

const {CleanWebpackPlugin} = require('clean-webpack-plugin')
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const path = require('path')
const configuration = require('./webpack.config.json')

const webpackConfiguration = {
    mode: configuration.debug ? 'development' : 'production',
    entry: {
        maps: path.resolve(__dirname, 'maps.js')
    },
    output: {
        path: path.resolve(__dirname, 'webpack-build'),
        filename: '[name].js'
    },
    optimization: {
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
        ]
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
          test: /\.(js)$/,
          use: [
            {
              loader: 'babel-loader',
              options: {
                cacheDirectory: true,
                presets: [
                  [
                    '@babel/preset-env',
                  ]
                ]
              }
            },
          ]
        },
        {
          test: /\.(css)$/,
          use: [
            {
              loader: MiniCssExtractPlugin.loader
            },
            {
              loader: 'css-loader',
              options: {
                sourceMap: configuration.debug
              }
            },
            {
              loader: 'resolve-url-loader',
              options: {
                debug: configuration.debug,
                sourceMap: configuration.debug
              }
            },
            {
              loader: 'sass-loader',
              options: {
                sourceMap: configuration.debug
              }
            }
          ]
        },
        {
          test: /\.(png|gif|jpg|jpeg|svg)$/,
          type: 'asset/resource',
          generator: {
            filename: 'images/[name][ext]',
          }
        }
      ]
    }
}
if (configuration.debug) {
    configuration.devtool = 'eval-source-map'
}

module.exports = webpackConfiguration