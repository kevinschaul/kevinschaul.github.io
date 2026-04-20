---
blogpost: true
date: '2024-12-05'
author: Kevin Schaul
category: til
title: git diff --ignore-all-space
tags: git, cli
slug: git-diff---ignore-all-space
---

# git diff --ignore-all-space

TIL `git diff` has an argument `--ignore-all-space` (or `-w`) which ignores whitespace. Perfect for when a bunch of code got indented but was otherwise unchanged -- the indentation changes will not get flagged!

