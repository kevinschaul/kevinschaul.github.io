# kevinschaul.github.io

## Installation

Requires Hugo and the R package `blogdown`

## Development

    blogdown::serve_site()

## Deploy

    blogdown::build_site()

### Create a new TIL

```
library(blogdown)
blogdown::new_post('your-new-til-slug-here', kind='til', subdir='til')
```
