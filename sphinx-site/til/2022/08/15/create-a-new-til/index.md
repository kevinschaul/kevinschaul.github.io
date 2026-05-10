---
blogpost: true
date: '2022-08-15'
author: Kevin Schaul
category: til
title: Create a new TIL
tags: R
slug: create-a-new-til
---

# Create a new TIL

To create a new TIL post using blogdown/Hugo:

```
library(blogdown)
blogdown::new_post('your-new-til-slug-here', kind='til', subdir='til')
```
