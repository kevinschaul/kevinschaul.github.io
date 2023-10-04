---
title: Writing a bad chess engine
date: '2023-10-04 16:45:00'
slug: writing-a-bad-chess-engine-for-uci-lichess
tags: [AI]
show_on_homepage: yes
blurb: 'My bot just plays a random move so far. Can you write a better one?'
tease: false
---

To stay sharp while on parental leave, I've been toying around with writing a chess engine. A bad one.

I am truly awful at chess. I know how the pieces are allowed to move, but that's it. If I am lucky enough to find myself ahead in an endgame, you can just move around randomly. I'll never figure out how to checkmate you.

But writing a program to play chess better than I can sounds ... pretty doable? If nothing else, it will be fun. And maybe I'll learn a thing about chess in the meantime.

[See the code behind badchess on GitHub](https://github.com/kevinschaul/badchess)

## How bots play chess: The UCI standard

I really didn't want to write the chess GUI -- that's too much like my day job. Thankfully there exists the [Universal Chess Interface (UCI)](https://backscattering.de/chess/uci/2006-04.txt). Essentially this protocol lets your chess engine interact with existing chess GUIs simply using text commands via standard input and output. There are a bunch of commands involved, but the few that seem to matter most are pretty simple.

Once you exchange a few commands to start a game, your engine just needs to react to a few commands:

- `position`: this defines where the pieces currently are on the chess board. UCI is stateless, so your program does not even need to keep track of this. You can just reinitialize your chess representation after each move, because the GUI will send this command.
- `go`: this tells your engine to start working calculating what move to run
       
Your engine calculates what move to run and then sends:

- `bestmove <move>`: this tells the GUI what move you are making

There are a lot more complicated options, but for a bad chess engine, that's about all I needed!

## Random move bot

I figured the easiest bot to implement would be one that makes a random move. I decided to write it in Python for two reasons. I didn't want to get bogged down learning a new language for this project, and there is a nice [chess library](https://python-chess.readthedocs.io/en/latest/index.html) that can help me narrow down what moves are legal given a board position. I originally figured I'd write this code myself, but I wanted to get UCI working as quickly as possible. Maybe I'll write my own the deeper I get.

Here is [the code to choose what move to play](https://github.com/kevinschaul/badchess/blob/3f05f619372a5bd7d83490eb8453fe3f0b952a92/badchess/badchess.py#L126). That needs some work!

## Playing against my bot

It's surprisingly easy to play against a bot that implements UCI. You just need to have a chess GUI, and point it to your engine. I've been using `xboard` to play. Here's how I can start my engine:

```
xboard -fcp badchess/badchess.py -fd . -fUCI
```

Easy enough. But I want to be able to play when I'm away from my computer, too. After doing a bunch of searching, I found out that [lichess.org](https://lichess.org/) supports bot accounts via [some python code on github](https://github.com/lichess-bot-devs/lichess-bot). And it can use UCI! Hooray for protocols.

Whenever the script is running on my computer, you can challenge [badchess_bot](https://lichess.org/@/badchess_bot) to a match. You will probably win.

## If you want to write your own bot

It took a while to figure out exactly what UCI commands I needed to implement and get something basic working. If you're interested in writing a chess engine, I think [this commit](https://github.com/kevinschaul/badchess/commit/3f05f619372a5bd7d83490eb8453fe3f0b952a92) would be a solid starting point. I wish I had this when I started.

Next up is the fun part -- figuring out how to make the engine play a better game. So far I can beat it pretty easily. I wonder how long until I can't.

If you write your own bot, let me know? I'd love to hear how it goes.
