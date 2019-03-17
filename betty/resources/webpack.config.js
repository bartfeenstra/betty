'use strict'

const CleanWebpackPlugin = require('clean-webpack-plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const path = require('path')

module.exports = {
  // @todo Once we have a mode (dev/prod) setting in our Betty configuration, optimize this.
  mode: 'development',
  entry: {
    betty: path.resolve(__dirname, 'input', 'js', 'betty.js')
  },
  output: {
    path: path.resolve(__dirname, 'output'),
    filename: '[name].js'
  },
  optimization: {
    // @todo Once we have a mode (dev/prod) setting in our Betty configuration, optimize this.
    minimize: false,
    splitChunks: {
      cacheGroups: {
        styles: {
          name: 'betty',
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
      path: path.resolve(__dirname, 'output'),
      filename: '[name].css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader']
      },
      // Ignore every file that's not CSS or JavaScript.
      {
        test: /^(?!.*(css|js)$).+$/,
        use: ['ignore-loader']
      }
    ]
  }
}
