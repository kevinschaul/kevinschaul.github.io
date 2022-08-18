---
title: Caching R code with cache_rds()
date: '2022-08-18'
slug: caching-r-code-with-cache-rds
tags: [R]
---

If you've got R code that takes a while to run (a query? complex analysis?), check out the fantastic [`cache_rds()`](https://bookdown.org/yihui/rmarkdown-cookbook/cache-rds.html) function from Yihui Xie’s `xfun` package.

Let's say you want to get census data from tidycensus, but you don’t want to keep hitting the API. Instead of writing:

```
cbsa_pop <- get_decennial(geography='cbsa', variables='P1_001N', year=2020)
```

You write:
```
cbsa_pop <- cache_rds({
  get_decennial(geography='cbsa', variables='P1_001N', year=2020)
})
```

The first time you run it, it will hit the census API like usual. But every subsequent time you run it, your computer will just read in the results from last time.

And here's the incredible thing imo: If you change your code (say you want 2010 data instead of 2020), the package is smart enough to know the code changed, so it will hit the API again.

[More documentation here](https://bookdown.org/yihui/rmarkdown-cookbook/cache-rds.html)
