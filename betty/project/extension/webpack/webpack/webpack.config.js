"use strict"

import CssMinimizerPlugin from "css-minimizer-webpack-plugin"
import MiniCssExtractPlugin from "mini-css-extract-plugin"
import path from "path"
import { readFileSync } from "node:fs"
import TerserPlugin from "terser-webpack-plugin"
import url from "node:url"
import webpack from "webpack"

const __dirname = url.fileURLToPath(new URL(".", import.meta.url))
const configuration = JSON.parse(readFileSync("./webpack.config.json"))

/**
 * Collect the scripts needed for all entry points, and build a loader.
 *
 * We do this, because page generation and the Webpack build take place concurrently for performance reasons.
 * When rendered, pages declare the Webpack extension entry points they need.
 * Using this Webpack plugin, we build a map of all scripts needed per entry point,
 * as well as a loader that is run on each page. The loader then imports the
 * scripts needed for the entry points declared on the page.
 */
class EntryScriptCollector {
    apply(compiler) {
        compiler.hooks.initialize.tap("ChunkCollector", () => {
            compiler.hooks.thisCompilation.tap(
                "ChunkCollector",
                (compilation) => {
                    compilation.hooks.processAssets.tapAsync(
                        {
                            name: "ChunkCollector",
                            stage: compiler.webpack.Compilation.PROCESS_ASSETS_STAGE_OPTIMIZE_INLINE,
                        },
                        (_, callback) => {
                            const extensionRegexp = /\.(js|mjs)(\?|$)/
                            const scripts = {}
                            for (const entryName of Object.keys(configuration.entry)) {
                                scripts[entryName] = compilation.entrypoints
                                    .get(entryName)
                                    .getFiles()
                                    .filter(entryFile => extensionRegexp.test(entryFile))
                                    .map(entryFile => `${configuration.rootPath}/${entryFile}?b=${configuration.jobContextId}`)
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
                                path.join("js", "webpack-entry-loader.js"),
                                new webpack.sources.RawSource(webpackEntryLoader),
                            )
                            return callback()
                        },
                    )
                },
            )
        })
    }
}

const webpackConfiguration = {
    mode: configuration.debug ? "development" : "production",
    devtool: configuration.debug ? "eval-source-map" : false,
    entry: configuration.entry,
    output: {
        path: path.resolve(__dirname, configuration.buildDirectoryPath),
        filename: "js/webpack/[name].js",
        publicPath: `${configuration.rootPath}/`,
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
                        comments: false,
                    },
                },
            }),
        ],
        splitChunks: {
            chunks: "all",
            cacheGroups: {
                // The resulting CSS files are one per entry point, and a single webpack-vendor.css.
                // This makes for easy and unconditional importing.
                vendorCss: {
                    test: /[\\/]node_modules[\\/].+?\.css$/,
                    name: "webpack-vendor",
                    priority: -10,
                },
                vendorJs: {
                    test: /[\\/]node_modules[\\/].+?\.js$/,
                    priority: -10,
                },
            },
        },
        runtimeChunk: "single",
    },
    plugins: [
        new EntryScriptCollector(),
        new MiniCssExtractPlugin({
            filename: "css/webpack/[name].css",
        }),
    ],
    module: {
        rules: [
            {
                test: /\.(js|ts)$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: "babel-loader",
                        options: {
                            cacheDirectory: path.resolve(__dirname, "cache"),
                            presets: [
                                [
                                    "@babel/preset-env", {
                                        debug: configuration.debug,
                                        modules: false,
                                        useBuiltIns: "usage",
                                        corejs: 3,
                                    },
                                ],
                                "@babel/preset-typescript",
                            ],
                        },
                    },
                ],
            },
            {
                test: /\.s?css$/,
                use: [
                    {
                        loader: MiniCssExtractPlugin.loader,
                    },
                    {
                        loader: "css-loader",
                        options: {
                            url: {
                                // Betty's own assets are generated through the assets file system,
                                // so we use Webpack for vendor assets only.
                                filter: (url, resourcePath) => resourcePath.includes("/node_modules/"),
                            },
                        },
                    },
                    {
                        loader: "postcss-loader",
                        options: {
                            postcssOptions: {
                                plugins: () => [
                                    require("autoprefixer"),
                                ],
                            },
                        },
                    },
                    {
                        loader: "sass-loader",
                    },
                ],
            },
            {
                test: /.*\.png|gif|jpg|jpeg|svg/,
                type: "asset/resource",
                generator: {
                    filename: "images/[hash][ext]",
                },
            },
            {
                test: /.*\.woff|woff2/,
                type: "asset/resource",
                generator: {
                    filename: "fonts/[hash][ext]",
                },
            },
            {
                test: /.*\.json/,
                type: "asset/source",
            },
        ],
    },
}

export default webpackConfiguration
