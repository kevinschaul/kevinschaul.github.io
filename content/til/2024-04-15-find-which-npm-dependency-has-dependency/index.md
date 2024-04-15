---
title: find-which-npm-dependency-has-dependency
author: ''
date: '2024-04-15'
slug: find-which-npm-dependency-has-dependency
categories: []
tags: [command line, js, nodejs]
---

Wow, a lifesaver command right here:

```
npm ls TROUBLESOME_PACKAGE
```

This will output a tree showing all of the node packages in your local project that depend on `TROUBLESOME_PACKAGE`. Dear lord have I needed this so many times.
