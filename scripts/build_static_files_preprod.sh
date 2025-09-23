#!/usr/bin/env bash

set -e

export NODE_ENV=preprod

# Build the css for the fastapi app
npm install

# build the css
npm run build

# build the react app
cd static/react-components
npm i
npm run tailwind
npm run scss
npm run build:preprod
cd ../..
