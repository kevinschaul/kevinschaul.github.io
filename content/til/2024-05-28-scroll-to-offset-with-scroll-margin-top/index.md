---
title: Scroll to offset with scroll-margin-top
date: 2024-05-28
slug: scroll-to-offset-with-scroll-margin-top
tags: [css]
comments:
  host: tilde.zone
  username: kevinschaul
  id: 112832028508681875
---

TIL there are some CSS properties that you can
set to adjust where a browser scrolls to when
scrolling to a div **without** ruining the
perfect spacing of your page!

Just add:

```
.my-element {
  scroll-margin-top: 60px;
}
```

And then this will scroll to 60px above the
element:

```
document.querySelector(".my-element")
  .scrollIntoView({ block: "start" })
```

