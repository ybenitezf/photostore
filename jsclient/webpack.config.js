var HtmlWebpackPlugin = require('html-webpack-plugin');
var path = require( 'path' );

module.exports = {
    context: __dirname,
    entry: {
      app: './src/app.js'
    },
    output: {
        path: path.resolve( __dirname, '../photostore/static/js' ),
        filename: '[name].js',
    },
    plugins: [new HtmlWebpackPlugin({
        inject: false,
        template: 'src/index.ejs',
        publicPath: '',
        filename: path.resolve( __dirname, '../photostore/templates/jsfiles.html' ),
    })],
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
        splitChunks: {
            chunks: 'all',
        },
    },
};
