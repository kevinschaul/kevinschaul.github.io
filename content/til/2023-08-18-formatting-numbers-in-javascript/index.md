---
title: Formatting numbers in javascript with Intl.NumberFormat()
author: ''
date: '2023-08-18'
slug: formatting-numbers-in-javascript
categories: []
tags: [js, frontend]
---

When formatting numbers for readability, say in a table, I've typically used [`d3-format`](https://github.com/d3/d3-format). But I could never get it to do exactly what I wanted.

Well I just learned there's a built-in for this now: [`Intl.NumberFormat()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat#options). The constructor takes two arguments: A locale (like 'en-us')`, and an extensive set of options. You can almost certainly get this to format numbers exactly how you want them.

In my case, I wanted 62,829,251,930 to become `62.8 billion`, and 5,760,646,320 to become `5.8 billion`. This formatter does it!

```
const format = Intl.NumberFormat('en-us', {
  // "compact" rounds and adds suffixes like "billion"
  notation: 'compact',
  
  // "long" makes it spell out "billion" rather than just "B"
  compactDisplay: 'long',
  
  // These ensure I get one digit after the decimal point,
  // which I want so the numbers line up nicely in a table
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

format.format(62829251930)
// => "62.8 billion"
```

[Read the docs here](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat)
