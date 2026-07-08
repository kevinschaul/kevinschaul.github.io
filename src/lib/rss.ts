import rss from "@astrojs/rss"
import { getCollection, type CollectionEntry } from "astro:content"
import type { APIContext } from "astro"
import MarkdownIt from "markdown-it"
import { sortByDateDesc } from "./collections"
import { absoluteUrl, entryPath, SITE } from "./site"
import { countWords, summarize } from "./text"

// linkify matches the GFM autolinking the pages use
const md = new MarkdownIt({ html: true, linkify: true })

// Hugo's .Summary is rendered HTML, so links in feed items stay clickable.
// Long bodies fall back to the plain-text 70-word summary.
function htmlSummary(body: string): string {
  if (countWords(body) <= 70) return md.render(body)
  return summarize(body)
}

export const RSS_LIMIT = 10

export type FeedEntry = CollectionEntry<"post" | "til" | "link" | "project">

export const SECTION_TITLES = {
  post: "Long posts",
  til: "TIL",
  link: "Short posts",
  project: "Projects",
} as const

export async function getAllFeedEntries(): Promise<FeedEntry[]> {
  return sortByDateDesc([
    ...(await getCollection("post")),
    ...(await getCollection("til")),
    ...(await getCollection("link")),
    ...(await getCollection("project")),
  ])
}

export async function getSectionFeedEntries(
  section: keyof typeof SECTION_TITLES,
): Promise<FeedEntry[]> {
  return sortByDateDesc(await getCollection(section))
}

export function feedOptions(
  context: APIContext,
  title: string,
  description: string,
  entries: FeedEntry[],
) {
  return {
    title,
    description,
    site: context.site?.toString() ?? SITE.url,
    items: entries.slice(0, RSS_LIMIT).map((entry) => ({
      title: entry.collection === "link" ? (entry.data.title ?? "") : entry.data.title || entry.id,
      pubDate: entry.data.date ? new Date(entry.data.date) : undefined,
      description: entry.data.blurb ?? htmlSummary(entry.body ?? ""),
      link: absoluteUrl(entryPath(entry)),
    })),
  }
}

export async function sectionFeed(
  context: APIContext,
  section: keyof typeof SECTION_TITLES,
) {
  const title = SECTION_TITLES[section]
  const descTitle = section === "til" ? title : title.toLowerCase()
  return rss(
    feedOptions(
      context,
      `${title} on ${SITE.title}`,
      `Recent ${descTitle} on ${SITE.title}`,
      await getSectionFeedEntries(section),
    ),
  )
}
