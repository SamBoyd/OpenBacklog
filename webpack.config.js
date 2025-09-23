const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { WebpackManifestPlugin } = require('webpack-manifest-plugin'); // Import the plugin

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  return {
    entry: {
      styles: './static/css/main.css' // Include your main CSS file
    },
    output: {
      filename: isProduction ? '[name].[contenthash].js' : '[name].js',
      path: path.resolve(__dirname, 'static/css/dist'), // Output to dist
      publicPath: '/static/dist/', // Important: Set the public path for assets
      clean: true, // Clean the output directory before each build
    },
    module: {
      rules: [
        {
          test: /\.css$/i,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            'postcss-loader', // Make sure postcss-loader runs after css-loader but before MiniCssExtractPlugin
          ],
        },
        // Add loaders for other file types (e.g., images, fonts) if needed
      ],
    },
    plugins: [
      new MiniCssExtractPlugin({
        filename: isProduction ? '[name].[contenthash].css' : '[name].css',
      }),
      // HtmlWebpackPlugin might still be useful for other purposes or if you serve static HTML sometimes
      // new HtmlWebpackPlugin({
      //   template: './templates/index.html', // Adjust if your base HTML template is elsewhere
      //   filename: 'index.html',
      //   chunks: ['main', 'styles'] // Specify which bundles to include
      // }),
      new WebpackManifestPlugin({
        fileName: 'asset-manifest.json', // Name of the manifest file
        publicPath: '/static/css/dist/',     // The public path prefix for assets (adjust if needed)
        generate: (seed, files, entrypoints) => {
          const manifestFiles = files.reduce((manifest, file) => {
            manifest[file.name] = file.path;
            return manifest;
          }, seed);
          // You might want to adjust this logic based on how you name your CSS entry point
          const cssFiles = entrypoints.styles ? entrypoints.styles.filter(
            fileName => fileName.endsWith('.css') && !fileName.endsWith('.map')
          ) : [];


          return {
            files: [],
            entrypoints: [],
            css: cssFiles, // Add a specific key for CSS entry points if needed
          };
        }
      })
      // Add other plugins if needed
    ],
    optimization: {
       // Optional: Helps manage dependencies and chunking
       splitChunks: {
         chunks: 'all',
       },
    },
    // Optional: Configure development server if needed
    // devServer: {
    //   static: './dist',
    // },
  };
};
