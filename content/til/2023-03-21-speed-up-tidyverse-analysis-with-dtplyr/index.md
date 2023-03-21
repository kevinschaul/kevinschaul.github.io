---
title: Speed up tidyverse analysis with dtplyr
date: '2023-03-21'
slug: speed-up-tidyverse-analysis-with-dtplyr
tags: [R]
---

I've got a ~15 million rows dataset that I need to do cleaning on. I'm a big [tidyverse](https://www.tidyverse.org/) fan, but `dplyr` is slower than `data.table`.

Well, TIL about [dtplyr](https://dtplyr.tidyverse.org/), which lets you write `dplyr` code but gain the speed of `data.table`:

```
library(data.table)
library(dtplyr)
library(dplyr, warn.conflicts=FALSE)

data_lazy <- data %>%
  lazy_dt(immutable=FALSE)

data_lazy %>%
  mutate(...) %>%
  group_by(column) %>%
  summarize(...) %>%
  as_tibble()
```

Take a look at the `immutable` argument in the docs. This runs soooo much faster.

Pair that with [a previous TIL about caching R code](https://www.kschaul.com/til/2022/08/18/caching-r-code-with-cache-rds/). Boom.

