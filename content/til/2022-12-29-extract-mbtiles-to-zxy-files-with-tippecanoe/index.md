---
title: Extract mbtiles into zxy files with tippecanoe
date: '2022-12-29'
slug: extract-mbtiles-to-zxy-files-with-tippecanoe
tags: [gis]
---

The next time you need to extract an .mbtiles file into tile files, reach for [tippecanoe](https://github.com/mapbox/tippecanoe). I’ve used it often for creating .mbtiles files but not for extracting tiles out of them.

It turns out you can the embedded command [`tile-join`](https://github.com/mapbox/tippecanoe#tile-join) for this task:

```
$ tile-join --force --no-tile-compression --no-tile-size-limit --output-to-directory tiles 2017-07-03_north-america.mbtiles --minimum-zoom 6 --maximum-zoom 10
```

h/t [yuiseki](https://scrapbox.io/yuiseki/How_to_create_your_own_vector_tile_web_maps)

