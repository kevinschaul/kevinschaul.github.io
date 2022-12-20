---
title: Writing D3 in React with an escape hatch
author: ''
date: '2022-12-19'
slug: writing-d3-in-react-with-an-escape-hatch
blurb: ""
categories: []
tags: [
    'D3',
    'React',
    'frontend',
]
---

Most of The Washington Post has moved to React for site rendering. This is hugely beneficial overall but for many graphics reporters it's yet another thing to learn to get stories published.

It's already overwhelming to learn HTML/CSS/JS, data analysis, some way to build charts, some mapping tool. I'm interested in lowering the barriers to entry for this field.

Fortunately there's a fairly simple pattern we can build into our tooling to bring back some simplicity of the pre-React frontend development.

Here are the React bits:

```{js}
// EscapedChart.js

import React, { useEffect, useRef } from 'react'

// chart.js is the file that'll use d3 to render a chart
import chart from './chart.js'

const EscapedChart = props => {
  const ref = useRef(null)
  
  useEffect(() => {
    // Store a local version of the element
    const el = ref.current
    
    // Run the `chart.js` file's default function
    chart(el)
    
    // As a cleanup, set the element's contents to be the empty string
    // This is helpful for hot reloading
    return function cleanup() {
      el.innerHTML = ''
    }
  }, [])
  
  return <div ref={ref} />
}
export default EscapedChart
```

And here's the part our graphics reporters can write d3 (or whatever) in:

```{js}
// chart.js

export default function chart(el) {
  // `el` is the element to put your chart in! go nuts with it
}
```

The code within the `chart` function should run just once -- React should not need to touch that div.

A more full example shows how to write d3 within React, without needing to know React:

```{js}
// chart.js

import { select } from 'd3-selection'
import { scaleLinear } from 'd3-scale'

export default function chart(el) {
  const { width } = el.getBoundingClientRect()
  const height = 50
  
  const data = [1, 2, 3, 5, 4]
  const barWidth = width / data.length
  
  const svg = select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
  
  const y = scaleLinear()
    .domain([0, 5])
    .range([0, height])

  svg.selectAll('rect')
    .data(data)
    .enter().append('rect')
    .attr('x', (d, i) => i * barWidth)
    .attr('width', barWidth)
    .attr('y', d => height - y(d))
    .attr('height', d => y(d))
}
```

That code is a lot friendlier looking to graphics folks than a bunch of refs and calls to `useEffect()`, I think.

