---
title: git diff --ignore-all-space
date: 2024-12-05
slug: git-diff---ignore-all-space
tags: [git, cli]
---

TIL `git diff` has an argument `--ignore-all-space` (or `-w`) which ignores whitespace. Perfect for when a bunch of code got indented but was otherwise unchanged -- the indentation changes will not get flagged!

