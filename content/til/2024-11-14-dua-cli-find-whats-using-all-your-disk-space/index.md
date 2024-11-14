---
title: "dua-cli: find what's using all your disk space"
date: 2024-11-14
slug: dua-cli-find-whats-using-all-your-disk-space
tags: [command line]
---

Next time you get that dreaded warning that your disk is nearly full, try out [dua-cli](https://github.com/Byron/dua-cli).

```
# Install
brew install dua-cli

# Run in interactive mode
dua interactive
```

Navigate around your file tree with arrow keys or vim bindings. Mark files for delete with "x". Press "q" to quit. The files you marked for deletion get printed to stdout. Theoretically you could pipe that to `xargs rm` but hell no. Just double check it, copy it to your clipboard and then:

```
# Prints what rm would do
pbpaste | xargs rm -v

# Actually remove the files
pbpaste | xargs rm
```
