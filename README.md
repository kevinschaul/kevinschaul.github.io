# kevinschaul.github.io

## Installation

    bundle install

## Development

    jekyll serve

## Deploy

    jekyll build

    aws s3 sync _site/ s3://kschaul --exclude ".DS_Store" --delete

