const {
  sentryWebpackPlugin
} = require("@sentry/webpack-plugin");

const path = require('path');
const CopyPlugin = require("copy-webpack-plugin");
const AssetsPlugin = require('assets-webpack-plugin');
const Dotenv = require('dotenv-webpack');
const TerserPlugin = require("terser-webpack-plugin");

var debug = process.env.NODE_ENV !== "prod" || process.env.NODE_ENV !== "preprod";

module.exports = {
  mode: debug ? 'development' : 'production',

  entry: {
    main: './renderers/renderMain.tsx',
  },

  output: {
    path: path.resolve(__dirname, 'build'),
    filename: '[name].[hash].js',
    chunkFilename: '[name].[chunkhash].js',
    publicPath: '/js/',
  },

  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
  },

  optimization: {
    minimize: !debug,
    minimizer: [
      new TerserPlugin({
        minify: TerserPlugin.uglifyJsMinify,
        terserOptions: {
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
    ],
  },

  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.scss$/,
        use: ['style-loader', 'css-loader', 'sass-loader'],
      },
      {
        test: /\.less$/,
        use: ['style-loader', 'css-loader', 'less-loader'],
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/[name].[hash][ext]',
        },
      },
    ],
  },

  optimization: {
    splitChunks: false, // Avoid splitting chunks to ensure separate files
  },

  plugins: [new CopyPlugin({
    patterns: [
      { from: 'styles/*.css', to: '[name].[contenthash].css' }, // Corrected 'to' path
    ]
  }), new Dotenv({
    path: '.env' + (process.env.NODE_ENV ? '.' + process.env.NODE_ENV : '.dev'),
    safe: true,
  }), new AssetsPlugin(), sentryWebpackPlugin({
    authToken: process.env.SENTRY_AUTH_TOKEN,
    org: "openbacklog",
    project: "react-frontend-app"
  }),
  ],

  devtool: debug ? "source-map" : false
};