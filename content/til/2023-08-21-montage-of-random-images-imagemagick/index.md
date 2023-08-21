---
title: Create a montage of images in random order with imagemagick
author: ''
date: '2023-08-21'
slug: montage-of-random-images-imagemagick
categories: []
tags: [command line]
---

It ain't pretty but this will let you use [ImageMagick's](https://imagemagick.org/script/index.php) montage command with a random order of images.

First, generate a text file with the image filenames in it, in random order. The `sed` commands put a `"` character at the beginning and end of the filename, otherwise ImageMagick freaks out.

```
ls my-images | \
  shuf | \
  sed 's/^/"/' | \
  sed 's/$/"/' > \
  randomly_ordered_images.txt
```

Then use that file of filenames as input, using the `@` operator.

```
magick montage @randomly_ordered_images.txt mosaic.jpg
```
