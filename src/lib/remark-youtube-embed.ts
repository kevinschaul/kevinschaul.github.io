import { visit } from "unist-util-visit"
import type { Root, Paragraph, Link, Html } from "mdast"

// Matches a paragraph that is *just* a YouTube link (nothing else in the
// sentence) and swaps it for a responsive embed, so authors can drop in a
// bare link instead of hand-writing the iframe wrapper markup.
const YOUTUBE_URL =
  /^https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube-nocookie\.com\/embed\/)([\w-]+)/

function extractStartEnd(url: URL): { start?: string; end?: string } {
  const start = url.searchParams.get("start") ?? url.searchParams.get("t")
  const end = url.searchParams.get("end") ?? undefined
  return {
    start: start ? start.replace(/s$/, "") : undefined,
    end,
  }
}

export function remarkYoutubeEmbed() {
  return (tree: Root) => {
    visit(tree, "paragraph", (node: Paragraph, index, parent) => {
      if (parent == null || index == null) return
      if (node.children.length !== 1 || node.children[0].type !== "link") return

      const link = node.children[0] as Link
      const match = link.url.match(YOUTUBE_URL)
      if (!match) return

      const id = match[1]
      const { start, end } = extractStartEnd(new URL(link.url))
      const params = new URLSearchParams()
      if (start) params.set("start", start)
      if (end) params.set("end", end)
      const query = params.toString()
      const src = `https://www.youtube-nocookie.com/embed/${id}${query ? `?${query}` : ""}`

      const html: Html = {
        type: "html",
        value:
          `<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">` +
          `<iframe src="${src}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen loading="lazy" title="YouTube video"></iframe>` +
          `</div>`,
      }

      parent.children[index] = html
    })
  }
}
