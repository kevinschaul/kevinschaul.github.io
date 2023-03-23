---
title: Write nested JSON with keys in R/tidyverse
date: '2023-03-22'
slug: write-nested-json-with-keys-in-r-tidyverse
tags: [R]
---



I always struggle to write JSON in R in exactly the format I need. I figured out a trick today to take a dataframe, nest it by a column and write it to a JSON with that column's values as keys.

To nest a table like this:


```
## # A tibble: 2 × 3
##   col_to_nest another_col a_third_col
##   <chr>             <dbl>       <dbl>
## 1 col_value_a     1213691 14616745740
## 2 col_value_b     1167231 13592103952
```


Try this:


```r
data %>%
  nest(.by=col_to_nest) %>%
  deframe() %>%
  map(unbox) %>%
  toJSON(pretty=T) # Or write_json('filename.json', pretty=T)
```

```
## {
##   "col_value_a": {
##       "another_col": 1213691,
##       "a_third_col": 14616745740
##     },
##   "col_value_b": {
##       "another_col": 1167231,
##       "a_third_col": 13592103952
##     }
## }
```

The piece I was missing was `deframe()`. This still feels super hacky though. Let me know if there's a better way!
