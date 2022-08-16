# kevinschaul.github.io

## Installation

Requires Hugo and the R package `blogdown`

## Development

    blogdown::serve_site() 

## Deploy

    blogdown::build_site()

    aws s3 sync public/ s3://kschaul --exclude ".DS_Store" --delete

