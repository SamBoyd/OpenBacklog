#!/usr/bin/env bash

echo "Building static files......."

# Build the css for the fastapi app
npm install

# build the css
npm run build

# build the react app
cd static/react-components
npm i
npm run tailwind
npm run scss
npm run build:dev
cd ../..

echo "Static files built successfully"
