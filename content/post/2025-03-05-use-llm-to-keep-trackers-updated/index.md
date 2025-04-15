---
title: "How I’m using an LLM to keep trackers updated"
date: "2025-03-05T16:53:43-06:00"
slug: "2025-03-05-use-llm-to-keep-trackers-updated"
tags: []
show_on_homepage: yes
blurb: ""
tease: false
---

**tldr; I am piping articles through an LLM to populate a spreadsheet that powers our tracker**

Last week I published [a piece](https://www.washingtonpost.com/politics/interactive/2025/trump-administration-actions/) tracking and categorizing what the Trump administration is doing. It's an exciting piece in many ways, but the most revelatory isn't on the page but is behind the scenes. I'm using an LLM to help me keep it updated -- in about 15 minutes a day.

- [A good task for AI](#a-good-task-for-AI)
- [The pipeline](#the-pipeline)
- [Evaluating the LLM with pytest-evals](#evaluating-the-llm-with-pytest-evals)
- [What's next'](#whats-next)

## A good task for AI

Trackers -- evergreen articles that are designed to be continuously updated -- can sometimes get a bad rap. They are difficult to design and promote. They typically require a lot of people spending time keeping track of updates. Often the work required ends up far outpacing the payoff.

In imagining this tracker, though, I had a few crucial (yet seemingly obvious) realizations. First, any time the Trump administration does something major, the Post publishes a story or an entry in a live updates file. All of these are easily downloadable via our internal article API. Second, LLMs understand text really, really well. If I could build a system that let me ask an LLM questions about our articles and store those results in a spreadsheet, I figured I would be cutting out most of the work of keeping a tracker updated. After a day of testing, I had a working prototype. A few weeks later, we published.

This case turned out to be perfect for an LLM. It should go without saying by now that these systems are not 100 percent trustworthy; they can make things up, have biases and are unpredictable. That's why I remain completely in control of what ends up published. The LLM helps, but it's ultimately up to me to mark articles for inclusion. Nothing is published automatically.

## The pipeline: Article API -> MySQL -> LLM -> Google Sheets

Every hour, my computer runs through the pipeline:

1. Download the latest articles into a mysql database
2. For each article, ask the LLM whether it is primarily about a new Trump administration action, yada yada. Store that result in the database. More on the prompting below.
3. Run some boring dedpulication
4. Sync the qualifying articles to our Google Sheet

From there, whenever we want to publish an update, I run through the Google Sheet, setting articles I want to include to TRUE. Once a day I also scroll through the rejected articles in my local database to see if the LLM missed anything obvious.

Finally I run our publish script, which downloads included entries from the Google Sheet. The whole process takes about 15 minutes.

## Evaluating the LLM with `pytest-evals`

This system worked surprisingly well using the first prompt I tried, but I am a numbers guy. How well did it work, really? You need to set up some test cases and an eval framework.

Creating my test cases was easy -- I have a database and Google Sheet full of articles, and a column with my ultimate determination on whether they should be included. These are my test cases. I knew I would continue updating this data, so I wrote a script that I can run any time to updating my test cases to include all of my decisions.

Being familiar with Python/pytest and being extremely particular about exactly how I wanted my evals to work, I was happy to find the absolute perfect plugin: [pytest-evals](https://github.com/AlmogBaku/pytest-evals). This lovely software lets you run your tests, saving the results to a json or csv file, and then lets you run whatever analysis you want across those tests.

I wrote my analysis script to test how different prompts would perform across a sample of my test cases. Claude helped me write [this analysis function](https://kschaul.com/jump-start/?path=/docs/python-pytest-evals-helpers--docs), which outputs a table like this:

```
===== Metrics by Prompt Template =====
Template ID  Sample Size  Accuracy   Precision  Recall     F1
-----------------------------------------------------------------
Template 1   200          84.00%     81.48%     88.00%     84.62%
Template 2   200          83.50%     79.13%     91.00%     84.65%
Template 3   200          81.00%     86.90%     73.00%     79.35%
```

Because this prompt determines what articles go into the Google Sheet, I prefer false positives over other errors. ~90 percent recall feels pretty good. But I still scroll through my local database before publishing to make sure I didn't miss something big.

For all of this, I am using The Post's internal LLM (which I think is Llama 3.1 70B). I do wonder how it would perform with some of the newer models.

## What's next

This was my first big use of AI for journalism. It was helpful to just try something and see where it ended up. Simon Willison's [llm](https://llm.datasette.io/en/stable/) tool was invaluable in this. It's one thing to play with LLMs via a chat interface, but it's entirely another to call them in code. Send the contents of an RSS feed, or the output of a unix command, or a web site ... it really gets your mind thinking through what's possible.

In the coming weeks, I'd love to see how well the LLM can do at categorizing these articles. So far I am doing that part manually. And any further improvements to the classification would be great. Should I consider a multi-step prompt? Different models? I'm not sure. But spending 15 minutes a day updating a tracker is a huge improvement.

Have you done something similar? I'd love to hear about it.
