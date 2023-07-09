---
title: Run a command when files change
author: ''
date: '2023-05-26'
slug: run-a-command-when-files-change
categories: []
tags: [command line]
---

TIL about [entr](https://github.com/eradman/entr), a command that lets you run arbitrary commands whenever files change.

I was working on a project where I had to run a build command whenever I saved a file. Once I installed `entr` (`brew install entr`), it took me about 5 seconds to figure out how to use it for this purpose.

```
find apple-news/ | entr -s 'npm run bespoke'
```

Any time a tile inside the directory `apple-news` changes, `npm run bespoke` gets run.

[Looks like](http://eradman.com/entrproject/) there are lots of other options for `entr` but I'll probably just stick to this pattern.
