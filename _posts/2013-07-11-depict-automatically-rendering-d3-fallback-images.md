---
layout: post
title:  "Depict - For automatically rendering d3.js fallback images"
date:   2013-07-11 22:39:02
slug: 2013-07-11-depict
---

While standards-compliant browsers are gaining marketshare, most media organizations still must support Internet Explorer 8, in some fashion. Creating fallback images for svg elements is a pain (though much easier with the handy [SVG Crowbar][svg-crowbar]).

Wouldn't it be great if a program could render out fallback images for SVGs automatically? [Depict][depict] aims to do just that.

(Don't get too excited; it still has a long way to go.)

As it stands today, `depict` is a command-line tool that converts an SVG element into a .png image. Fill in a JavaScript function with some [d3.js][d3] code, and the script will do the rest.

The depict package comes with `depict-init`, which sets up example code that works out of the box with `depict`.

The tool isn't especially useful today, but the potential is there. If you have any ideas or want to collaborate, let's get in touch.

[Depict on GitHub][depict]

[svg-crowbar]: http://nytimes.github.io/svg-crowbar/
[depict]: https://github.com/kevinschaul/depict
[d3]: http://www.kevinschaul.com/2013/07/11/depict-automatically-rendering-d3-fallback-images/d3js.org

