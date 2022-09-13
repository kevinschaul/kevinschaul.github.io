---
title: Coloring emoji/unicode characters on iOS Safari
date: '2022-09-13'
slug: coloring-emoji-unicode-characters-on-ios-safari
tags: [frontend]
---

Unicode characters such as ■ (black square U+25A0) can be super useful to use for icons without needing to load an icon font. And they can typically be styled using CSS, like: `color: steelblue;`.

But on iOS safari (and likely Android and other devices), these are rendered in the cartooney, emoji style — which means trying to color them with CSS doesn’t work.

Fortunately there is an easy (but cryptic) fix: Simply append `&#xFE0E;` immediately following your unicode character, like `■&#xFE0E;`. The code modifies the previous character to be rendered in text style rather than emoji style.

[HT Matais Singers](https://mts.io/2015/04/21/unicode-symbol-render-text-emoji/)
