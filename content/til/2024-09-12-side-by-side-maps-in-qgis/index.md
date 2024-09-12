---
title: Side-by-side maps in QGIS
date: 2024-09-12
slug: side-by-side-maps-in-qgis
tags: [qgis]
---

TIL you can view multiple maps at the same time in QGIS -- for example if you want to compare two layers.

1. Create a new map view: View -> New Map View. Drag that to the side to dock it.
2. Create a new map theme: In your layers panel, click the eyeball -> Add Theme. In your new map view, click the eyeball -> select this new theme.
3. Synchronize the maps: In your new map view, click the settings wrench -> check Synchronize View Center and Synchronize scale

h/t [opensourceoptions.com](https://opensourceoptions.com/split-screen-view-and-multiple-map-views-in-qgis/)
