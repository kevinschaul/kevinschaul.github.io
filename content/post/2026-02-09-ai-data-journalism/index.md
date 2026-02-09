---
title: "How I used Claude Code in a real data journalism project"
date: "2026-02-09T11:20:00-06:00"
slug: "2026-02-09-ai-data-journalism"
tags: [ai]
show_on_homepage: yes
blurb: "When you’re doing data journalism, vibes are not enough."
tease: false
images:
  - spreadsheets.jpg
---

This morning three colleagues and I [published a story](https://www.washingtonpost.com/technology/2026/02/09/trump-administration-ai-push/) outlining how the federal government is using AI. Here’s how I used Claude Code to help.

Agencies are required to publish a spreadsheet of AI use cases. Unfortunately (and unsurprisingly) each agency posts them in a different place on their website, in a different file format, using different column names and values. OMB will eventually consolidate these, but why wait when we can do it ourselves?

![A small sample of the messiness: Three spreadsheets, each with different headers and columns](spreadsheets.jpg)

Locating, consolidating and cleaning disparate data sources is a classic data journalism task. It’s also a perfect use-case for “agentic” AI systems like Claude Code. Having done similar projects many times before, I had a good sense of the steps and how to structure the files to ensure auditability and idempotence. 

Here’s the prompt I gave to Claude Code (Opus 4.5):

> for every agency in data/raw/agencies.txt:
> 1. search the internet for “AGENCY_NAME AI use inventory". each agency should have an official .gov page outlining ai uses.
> 2. find in that page the downloadable csv/excel file for the agency use cases. save it in data/raw.
> 3. when you have found them all, write a python script that converts them all into one csv file. make it easy to read so I can double check that every agency is correct. the columns should all include the same information even if they are not named exactly the same. keep a log of any questions or potentially confusing situations that I should double check.

That churned for about 10 minutes before I hit the usage limit 😭. The prompt fired off a ton of web searches but none completed step 2 by the time I had to quit. I should have had it fill out a spreadsheet as it went. Save all incremental progress to file.

Since I also have a ChatGPT subscription, I switched to Codex and tried just step 1, asking to save progress to a csv. That worked for most agencies. I cleaned that csv up by hand, deleting some results from 2024 and a few other silly errors.

After lunch, I turned back to Claude Code, asking to write a script to download all files from the csv. That worked perfectly. Don’t try to one-shot a complicated process. Go one step at a time.

Next I asked Claude Code to perform the consolidation step. This was the big timesaver. Claude started a loop where it read a few of the raw data files, wrote a script to put them together, ran it for all files, tweaked the script, and on and on. The result is [a reasonable python script](https://github.com/kevinschaul/2025-Federal-Agency-AI-Use-Case-Inventory/blob/main/scripts/consolidate_inventories.py) that would have been horribly tedious to write by hand. I also set up a script to search for new files and download them, and made sure the consolidate script would be rerun without breaking.

To be clear, hell yes I read the generated code. When you’re doing data journalism, vibes are not enough. I have been told “You’re absolutely right!” far too many times by these tools to trust them. Likewise I would not trust an LLM to read the data directly. But having AI write and execute code that can be audited? I’m quite comfortable with that.

After a lot more spot checking, it was ready to share with the team for further analysis. Not bad for a few day’s work.

