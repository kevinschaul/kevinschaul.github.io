import { getCollection, type CollectionEntry } from "astro:content"
import type { APIContext } from "astro"
import { notDraft, sortByDateDesc } from "./collections"
import { absoluteUrl, entryPath, SITE } from "./site"
import { summarize } from "./text"

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
    ...(await getCollection("post")).filter(notDraft),
    ...(await getCollection("til")).filter(notDraft),
    ...(await getCollection("link")).filter(notDraft),
    ...(await getCollection("project")).filter(notDraft),
  ])
}

export async function getSectionFeedEntries(
  section: keyof typeof SECTION_TITLES,
): Promise<FeedEntry[]> {
  return sortByDateDesc((await getCollection(section)).filter(notDraft))
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
      description: entry.data.blurb ?? summarize(entry.body ?? ""),
      link: absoluteUrl(entryPath(entry)),
    })),
  }
}
