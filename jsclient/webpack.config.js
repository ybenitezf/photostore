const path = require( 'path' );

module.exports = {
    context: __dirname,
    entry: {
      app: './src/app.js'
    },
    output: {
        path: path.resolve( __dirname, '../photostore/static/js' ),
        filename: '[name].js',
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: 'babel-loader',
            },
            {
                test: /\.css$/i,
                use: ['style-loader', 'css-loader'],
            }
        ]
    },
    externals: {
      jquery: 'jQuery'
    },
    optimization: {
        minimize: true,
        splitChunks: {
            chunks: 'all',
        }
    }
};
