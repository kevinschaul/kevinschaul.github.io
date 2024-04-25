---
title: Stitches inline media queries
date: 2024-04-25
slug: stitches-inline-media-queries
tags: [js, stitches]
---

Finally figured out how to write inline media queries in
[Stitches](https://stitches.dev/docs/responsive-styles):

    const Button = styled('button', {
      background: 'blue',
      '@media (max-width: 462px)': {
        background: 'orange',
      },
    })

You can just write the media query directly in here. No needing to fuss with
creating global breakpoints when you just need something small to happen at a
specific width. Wow.

h/t claude.ai, which I've been using a ton of lately.
