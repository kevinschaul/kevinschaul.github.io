# kevinschaul.github.io

## Installation

Requires Node.js 20+.

```
npm install
```

## Development

```
npm run dev
```

## Deploy

Happens automatically with GitHub Pages. The workflow builds the Astro site and
publishes `dist/`.

### `til` utility

Install with:

```
cp til ~/.local/bin/til
```

Then, create a new TIL with:

```
til 'Title for the post'
```

The post will be created and opened in your $EDITOR.

### Create a new post

```
just post
```

### Create a new project

- `tease.png` size: 441x152

### Embed a YouTube video

Paste the video link on its own line (a `youtube.com/watch?v=`, `youtu.be/`,
or embed URL) — it's automatically turned into a responsive embed. `start`/
`end`/`t` query params carry through if you want a specific clip:

```
https://youtu.be/dQw4w9WgXcQ
```
