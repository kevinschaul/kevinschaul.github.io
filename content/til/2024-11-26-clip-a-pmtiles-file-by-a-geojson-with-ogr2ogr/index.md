---
title: Clip a pmtiles file by a geojson with ogr2ogr
date: 2024-11-26
slug: clip-a-pmtiles-file-by-a-geojson-with-ogr2ogr
tags: [gis, command line]
---

Like the title says. Clip a .pmtile file by a geojson with ogr2ogr:

```
# ogr2ogr -clipsrc CLIP_SHAPE OUTPUT INPUT
ogr2ogr -clipsrc us.geojson osm-place-us.pmtiles osm-place-world.pmtiles
```

