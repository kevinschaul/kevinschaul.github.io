# kevinschaul.github.io

## Installation

Requires Hugo and the R package `blogdown`

## Development

    blogdown::serve_site()

## Deploy

    blogdown::build_site()

### `til` utility

Install with:

```
cp til ~/.local/bin/til
```

Then, create a new TIL with:

```
til 'Title for the post'
```

The post will be created and opened in your $EDITOR.

### Create a new post through blogdown

```
library(blogdown)
blogdown::new_post('your-new-til-slug-here', kind='til', subdir='til')
```
