import type { CollectionEntry } from "astro:content"
import { datedPath, sectionPath, tagPath, hugoDateParts, urlize } from "./urls"

export const SITE = {
  title: "Kevin Schaul",
  description: "Visual journalist/hacker covering AI",
  url: "https://kschaul.com",
  image: "https://kschaul.com/social.jpg",
  cloudflareToken: "570754c1f24b46e79d87fb55ce121c4d",
  nav: [
    { label: "About", href: "/contact/" },
    { label: "LLM evals", href: "https://kschaul.com/llm-evals/" },
    { label: "Follow", href: "/follow/" },
  ],
}

type Section = "post" | "til" | "link" | "project"
type Entry = CollectionEntry<Section>

export function entrySlug(entry: Entry): string {
  return urlize(entry.data.slug ?? entry.id)
}

export function absoluteUrl(path: string): string {
  return new URL(path, SITE.url).toString()
}

export function entryPath(entry: Entry): string {
  if (entry.collection === "post" || entry.collection === "til") {
    return datedPath(entry.collection, entrySlug(entry), entry.data.date)
  }
  return sectionPath(entry.collection, entrySlug(entry))
}

export function tagUrl(tag: string): string {
  return tagPath(tag)
}

export function datedParams(entry: CollectionEntry<"post" | "til">) {
  const parts = hugoDateParts(entry.data.date)
  if (!parts) return null
  return {
    year: parts.y,
    month: parts.m,
    day: parts.d,
    slug: entrySlug(entry),
  }
}

export function sectionParams(entry: CollectionEntry<"link" | "project">) {
  return { slug: entrySlug(entry) }
}
