---
blogpost: true
date: '2024-04-20'
author: Kevin Schaul
category: til
title: Fix FIPS codes in R with str_pad()
tags: R
slug: fix-fips-codes-in-r-with-str-pad
---

FIPS codes for U.S. counties need leading zeros, but often your data doesn't have them. Someone down the line may have read them in as numbers, which removed the leading zeroes.

stringr makes fixing that a breeze:

```
data %>%
  mutate(
    fips = str_pad(fips, 5, pad="0")
  )
```

h/t [Luis Melgar](https://www.lmelgar.me/)
