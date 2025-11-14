const {
  sentryWebpackPlugin
} = require("@sentry/webpack-plugin");

const path = require('path');
const webpack = require('webpack');
const CopyPlugin = require("copy-webpack-plugin");
const AssetsPlugin = require('assets-webpack-plugin');
const Dotenv = require('dotenv-webpack');
const TerserPlugin = require("terser-webpack-plugin");

var debug = process.env.NODE_ENV !== "prod" || process.env.NODE_ENV !== "preprod";

// ============================================================================
// DEBUG LOGGING
// ============================================================================
const envPath = process.env.CLUSTER_NAME
  ? `.env.cluster-${process.env.CLUSTER_NAME}`
  : '.env' + (process.env.NODE_ENV ? '.' + process.env.NODE_ENV : '.dev');

console.log('='.repeat(70));
console.log('WEBPACK BUILD DEBUG INFO');
console.log('='.repeat(70));
console.log(`CLUSTER_NAME env var: ${process.env.CLUSTER_NAME || 'NOT SET'}`);
console.log(`NODE_ENV env var: ${process.env.NODE_ENV || 'NOT SET'}`);
console.log(`Env file path being loaded: ${envPath}`);
console.log(`Current working directory: ${process.cwd()}`);
console.log(`__dirname: ${__dirname}`);

// Try to read the env file to show its contents
const fs = require('fs');
const path_module = require('path');
const envFilePath = path_module.join(__dirname, envPath);
console.log(`Full env file path: ${envFilePath}`);
try {
  if (fs.existsSync(envFilePath)) {
    console.log(`✓ Env file EXISTS at ${envFilePath}`);
    const fileContents = fs.readFileSync(envFilePath, 'utf8');
    console.log('Env file contents:');
    console.log(fileContents);
  } else {
    console.log(`✗ Env file NOT FOUND at ${envFilePath}`);
  }
} catch (err) {
  console.log(`Error reading env file: ${err.message}`);
}
console.log('='.repeat(70));

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

  plugins: [
    new CopyPlugin({
      patterns: [
        { from: 'styles/*.css', to: '[name].[contenthash].css' }, // Corrected 'to' path
      ]
    }),
    new Dotenv({
      // Load cluster-specific env file if CLUSTER_NAME is provided, otherwise fallback to NODE_ENV-based
      path: process.env.CLUSTER_NAME
        ? `.env.cluster-${process.env.CLUSTER_NAME}`
        : '.env' + (process.env.NODE_ENV ? '.' + process.env.NODE_ENV : '.dev'),
      safe: false,
    }),
    new AssetsPlugin(), sentryWebpackPlugin({
      authToken: process.env.SENTRY_AUTH_TOKEN,
      org: "openbacklog",
      project: "react-frontend-app"
    }),
  ],

  devtool: debug ? "source-map" : false
};