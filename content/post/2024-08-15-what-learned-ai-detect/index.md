---
title: "What I learned working on the AI detection story"
date: "2024-08-15T10:08:17-05:00"
slug: "2024-08-15-what-learned-ai-detect"
tags: []
show_on_homepage: yes
blurb: "The new CSS units, computational reporting, discrete scrollytelling, autoplay video"
tease: false
---

[This AI detection story](https://www.washingtonpost.com/technology/interactive/2024/ai-detection-tools-accuracy-deepfakes-election-2024/) is one of my favorite things I’ve published in a while. Here are some things I learned putting it together:


**The new CSS units are a godsend**
Anyone who has built fullscreen web content for mobile knows the pain of the browser resizing as users scroll up and down. The new CSS units lvh, svh and dvh are incredibly useful. Use `svh` if you need your content visible even if the user is scrolling up, or `lvh` if you just want to ensure the largest screen height will be covered.

A bonus tip: [Here‘s a React hook to get those units in JavaScript](https://kschaul.com/jump-start/?path=/docs/react-useviewportheightunits--docs).


**There’s power in computational reporting**
I read (probably too many) papers about deepfake creation and detection to understand how this all worked. I ran or reimplemented a bunch of detection techniques and then tried them out across a bunch of deepfakes and legitimate videos. That work literally appears in the story’s visuals but also informed the questions we asked experts. We went deep. One source said our interview was one of the most technical he’s had. I took that as a compliment.


**I tried a discrete scroll experience in the topper**
We’re all sick of scrollytelling but it just feels so right when you have visuals that flow into each other. This topper is my attempt to make the actual scrolling part less painful. I’m very curious to hear how you think it works. I built it with SwiperJS, with some custom logic to enable and disable the scroll wheel. I tried to balance making sure you saw each step with letting you move on to the rest of the story.


**Autoplay video experiences remain difficult to build**
Last time I built a big autoplay video experience was [a few years ago](https://www.washingtonpost.com/graphics/world/border-barriers/global-illegal-immigration-prevention/) — there’s a lot of jQuery in that project. Things have both gotten easier and trickier since then. The new trick was supporting devices like iPhones in low power mode, where autoplay video does not work.

