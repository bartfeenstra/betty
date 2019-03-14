'use strict';

const path = require('path');
module.exports = {
    mode: 'production',
    entry: path.resolve(__dirname, 'js', 'betty.js'),
    output: {
        path: path.resolve(__dirname),
        filename: 'betty.js'
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: ['css-loader']
            },
            {
                test: /\.(png|jpg|gif)$/,
                use: ['file-loader'],
            },
        ]
    }
};
